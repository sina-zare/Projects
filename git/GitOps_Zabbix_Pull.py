#!/usr/bin/env python3
import os
import shutil
import subprocess
import logging
from datetime import datetime
import sys
import time
import socket

# --- Configuration ---
ZABBIX_SERVER = '-'.join((socket.gethostname().split('-'))[:2]).lower() # e.g. "me-zabbix"
ZABBIX_SERVER_REPO_PATH = f"{ZABBIX_SERVER}/configs"
REPO_PATH = "/opt/scripts/pull-push-config/git-files"   # local working copy of the git repo
GITLAB_URL = "https://me-gitlab.abramad.com/operation/sysops/zabbix.git"
BRANCH = "main"
LOG_FILE = "/opt/scripts/pull-push-config/logs/logger_pull.log"
ETC_ZABBIX = "/etc/zabbix"


# --- Logging setup ---
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

def run(cmd, cwd=None):
    """Run a shell command safely, log output and print to console.
    Sanitizes displayed git URLs so token is not printed.
    """
    # sanitize display name for git network commands
    if cmd.startswith("git push"):
        display_cmd = "git push"
    elif cmd.startswith("git pull"):
        display_cmd = "git pull"
    elif cmd.startswith("git clone"):
        display_cmd = "git clone"
    elif "fetch" in cmd:
        display_cmd = "git fetch"
    else:
        display_cmd = cmd

    logging.info(f"Running: {display_cmd}")
    print(f">>> {display_cmd}")

    result = subprocess.run(
        cmd, shell=True, cwd=cwd,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )

    if result.stdout:
        logging.info(result.stdout.strip())
        print(result.stdout.strip())

    # treat stderr as info when returncode == 0 (git often writes status to stderr)
    if result.returncode == 0:
        if result.stderr and result.stderr.strip():
            logging.info(result.stderr.strip())
            print(result.stderr.strip())
    else:
        # failing commands report stderr as error
        if result.stderr and result.stderr.strip():
            logging.error(result.stderr.strip())
            print(result.stderr.strip())
        raise RuntimeError(f"Command failed: {cmd}\n{result.stderr}")

    return result.stdout.strip()

def ensure_repo():
    """Clone repo if not present, otherwise fetch & reset/pull latest."""
    token = os.environ.get("GITLAB_TOKEN")
    if not token:
        raise EnvironmentError("GITLAB_TOKEN not set in environment!")

    auth_url = GITLAB_URL.replace("https://", f"https://oauth2:{token}@")

    if not os.path.exists(REPO_PATH):
        os.makedirs(REPO_PATH, exist_ok=True)

    gitdir = os.path.join(REPO_PATH, ".git")
    if not os.path.exists(gitdir):
        # clone repo into REPO_PATH (empty dir)
        run(f"git clone {auth_url} {REPO_PATH}")
        # set checked out branch if needed
        run(f"git -C {REPO_PATH} switch -c {BRANCH} || true")
    else:
        # fetch and update remote branch safely
        try:
            # fetch remote branch and update origin/main explicitly
            run(f"git -C {REPO_PATH} fetch {auth_url} {BRANCH}:refs/remotes/origin/{BRANCH}")
            # ensure we're on the branch
            run(f"git -C {REPO_PATH} checkout {BRANCH}")
            # hard-reset local working tree to the now-updated origin/<BRANCH>
            run(f"git -C {REPO_PATH} reset --hard origin/{BRANCH}")
        except RuntimeError as e:
            logging.warning(f"git fetch/pull encountered an issue: {e}. Trying pull with merge fallback.")
            run(f"git -C {REPO_PATH} pull {auth_url} {BRANCH}")

def find_server_dir():
    """Return the path to the configs directory for this ZABBIX_SERVER."""
    server_directory = os.path.join(REPO_PATH, ZABBIX_SERVER_REPO_PATH)
    if os.path.isdir(server_directory):
        return server_directory
    else:
        raise FileNotFoundError(f"Configs directory not found: {server_directory}")


def locate_config_files(server_dir):
    """Return paths to Zabbix config files in the standard configs/ directory."""
    files = {
        "server": os.path.join(server_dir, "zabbix_server.conf"),
        "agent": os.path.join(server_dir, "zabbix_agent2.conf")
    }
    return files


def backup(path):
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    bak = f"{path}.bak.{ts}"
    shutil.copy2(path, bak)
    logging.info(f"Backed up {path} -> {bak}")
    return bak

def restore(backup_path, dest):
    shutil.copy2(backup_path, dest)
    logging.info(f"Restored {backup_path} -> {dest}")

def apply_configs(found):
    """Copy the found config files into /etc/zabbix, validating before finalizing."""
    # track backups to remove later or to restore on failure
    backups = []
    try:
        # server config
        if found["server"]:
            dest = os.path.join(ETC_ZABBIX, "zabbix_server.conf")
            if os.path.exists(dest):
                backups.append((backup(dest), dest))
            shutil.copy2(found["server"], dest)
            logging.info(f"Copied server config {found['server']} -> {dest}")
            print(f">>> Copied server config to {dest}")
            # validate
            run(f"zabbix_server -c {dest} -T")

        # agent config
        if found["agent"]:
            dest = os.path.join(ETC_ZABBIX, "zabbix_agent2.conf")
            if os.path.exists(dest):
                backups.append((backup(dest), dest))
            shutil.copy2(found["agent"], dest)
            logging.info(f"Copied agent config {found['agent']} -> {dest}")
            print(f">>> Copied agent config to {dest}")
            # validate
            run(f"zabbix_agent2 -c {dest} -T")

        # if we reach here, validations passed
        # remove backups
        for bkp, _ in backups:
            try:
                os.remove(bkp)
                logging.info(f"Removed backup {bkp}")
            except Exception:
                pass

        logging.info("✅ Configs applied and validated successfully")
        print("✅ Configs applied and validated successfully")

    except Exception as e:
        logging.error(f"Configuration not applied: {e}")
        print(f"Error during apply: {e}\nRestoring backups...")
        # restore backups in reverse order
        for bkp, dest in reversed(backups):
            try:
                restore(bkp, dest)
            except Exception as re:
                logging.error(f"Failed to restore {bkp} to {dest}: {re}")
        raise


logging.info("=== Starting Zabbix config pull ===")
try:
    ensure_repo()
    server_dir = find_server_dir()
    if not server_dir:
        raise FileNotFoundError(f"Server directory '{ZABBIX_SERVER_REPO_PATH}' not found in repo '{REPO_PATH}'")

    logging.info(f"Found server dir: {server_dir}")
    print(f">>> Found server dir: {server_dir}")

    found = locate_config_files(server_dir)
    logging.info(f"Located configs: {found}")
    print(f">>> Located configs: {found}")

    if not found["server"] and not found["agent"]:
        raise FileNotFoundError("No zabbix_server.conf or zabbix_agent2.conf found for this server in the repo")

    # apply (copy + validate + backup/restore)
    apply_configs(found)

except Exception as e:
    logging.error(f"❌ Error: {e}")
    print(f"Error: {e}")
    sys.exit(1)
else:
    logging.info("✅ Script finished successfully")
    sys.exit(0)

