#!/usr/bin/env python3
import os
import shutil
import subprocess
import logging
from datetime import datetime
import socket
import glob

# --- Configuration ---
SERVER_NAME_FULL = (socket.gethostname()).lower()
SERVER_NAME_SUM = '-'.join((SERVER_NAME_FULL.split('-'))[:2]) # e.g. "me-zabbix"
SERVER_REPO_PATH = f"{SERVER_NAME_SUM}/{SERVER_NAME_FULL}"
REPO_PATH = f"/opt/scripts/pull-push-config/git-files"
FILES_TO_COPY = [
    "/etc/patroni/*",
]
GITLAB_URL = "https://me-gitlab.abramad.com/operation/sysops/patroni.git"
BRANCH = "main"
LOG_FILE = "/opt/scripts/pull-push-config/logs/logger_push.log"


# --- Logging setup ---
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)


def run(cmd, cwd=None):
    """Run a shell command safely, log output, and print it to the console."""
    display_cmd = "git push" if cmd.startswith("git push") else ("git pull" if cmd.startswith("git pull") else cmd)
    logging.info(f"Running: {display_cmd}")
    print(f">>> {display_cmd}")

    result = subprocess.run(
        cmd, shell=True, cwd=cwd,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )

    # Log stdout (always informational)
    if result.stdout:
        logging.info(result.stdout.strip())
        print(result.stdout.strip())

    # Log stderr:
    if result.returncode == 0:
        # Success, so stderr likely contains informational output (e.g., git push)
        if result.stderr.strip():
            logging.info(result.stderr.strip())
            print(result.stderr.strip())
    else:
        # Only log as error when the command failed
        if result.stderr.strip():
            logging.error(result.stderr.strip())
            print(result.stderr.strip())
        raise RuntimeError(f"Command failed: {cmd}\n{result.stderr}")

    return result.stdout.strip()



#def copy_files():
#    """Copy Zabbix config files to repo directory."""
#    for src in FILES_TO_COPY:
#        dest = os.path.join(f"{REPO_PATH}/{SERVER_REPO_PATH}", os.path.basename(src))
#        if os.path.exists(src):
#            shutil.copy2(src, dest)
#            logging.info(f"Copied {src} → {dest}")
#        else:
#            logging.warning(f"Source file not found: {src}")


def copy_files():
    """Copy config files to repo directory."""
    dest_dir = os.path.join(REPO_PATH, SERVER_REPO_PATH)
    os.makedirs(dest_dir, exist_ok=True)

    for pattern in FILES_TO_COPY:
        for src in glob.glob(pattern):  # expand wildcards
            if os.path.isfile(src):  # only copy files
                dest = os.path.join(dest_dir, os.path.basename(src))
                shutil.copy2(src, dest)
                logging.info(f"Copied {src} → {dest}")
            elif os.path.isdir(src):  # optionally handle subdirectories
                dest_subdir = os.path.join(dest_dir, os.path.basename(src))
                shutil.copytree(src, dest_subdir, dirs_exist_ok=True)
                logging.info(f"Copied directory {src} → {dest_subdir}")
            else:
                logging.warning(f"Skipping unknown file type: {src}")



def setup_git_identity():
    """Set Git user name and email locally for the repo."""
    try:
        run('git config user.name "sysops-svc"', cwd=REPO_PATH)
        run('git config user.email "sysops-svc@abramad.com"', cwd=REPO_PATH)
        logging.info("✅ Git identity set for this repo")
    except RuntimeError as e:
        logging.error(f"Failed to set Git identity: {e}")
        raise

def git_pull():
    """Pull latest changes from GitLab before pushing."""
    token = os.environ.get("GITLAB_TOKEN")
    if not token:
        raise EnvironmentError("GITLAB_TOKEN not set in environment!")

    auth_url = GITLAB_URL.replace("https://", f"https://oauth2:{token}@")

    try:
        run(f"git pull {auth_url} {BRANCH}", cwd=REPO_PATH)
        logging.info("✅ Repository successfully updated with latest remote changes")
    except RuntimeError as e:
        logging.warning(f"⚠️ Pull failed (possibly no changes to fetch): {e}")

def git_push():
    """Commit and push all changes to GitLab."""
    token = os.environ.get("GITLAB_TOKEN")
    if not token:
        raise EnvironmentError("GITLAB_TOKEN not set in environment!")

    # Use token-based authentication (embed in remote URL)
    auth_url = GITLAB_URL.replace("https://", f"https://oauth2:{token}@")

    run("git add .", cwd=REPO_PATH)
    commit_message = f"Patroni config update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    run(f"git commit -m '{commit_message}' || echo 'No changes to commit'", cwd=REPO_PATH)
    run(f"git push {auth_url} {BRANCH}", cwd=REPO_PATH)
    logging.info("✅ Push completed successfully")


try:
    logging.info("=== Starting Patroni config push ===")
    os.chdir(REPO_PATH)
    copy_files()
    setup_git_identity()   # <-- set Git identity locally
    git_push()
except Exception as e:
    logging.error(f"❌ Error: {e}")
    print(f"Error: {e}")
else:
    logging.info("✅ Script finished successfully")

