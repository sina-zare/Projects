#!/usr/bin/env python3
import os
import shutil
import subprocess
import logging
from datetime import datetime
import glob
import socket

'''
    Config files:
    /etc/bind/named.conf
                   .conf.local
                   .conf.local.rev
                   .conf.options
    
    Zones:
    /etc/bind/forwardzones
    /etc/bind/reversezones
'''

# --- Configuration ---
#SERVER_NAME_FULL = (socket.gethostname()).lower()
#SERVER_NAME_SUM = '-'.join((SERVER_NAME_FULL.split('-'))[:2]) # e.g. "me-zabbix"
#SERVER_REPO_PATH = f"{SERVER_NAME_SUM}/{SERVER_NAME_FULL}"
REPO_PATH = f"/opt/scripts/pull-push-config/git-files"

GITLAB_URL = "https://gitlab.abramad.com/abramad/sysops/bind.git"
PROJECT = GITLAB_URL.split("/")[-1].split(".")[0]
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


def copy_files(src_patterns, dest_path, preserve_tree=False):
    """
    Copy files/directories matched by src_patterns into dest_path.

    - src_patterns: str or list[str] (e.g. "/opt/repo/*" or ["/a/*", "/b.conf"])
    - dest_path: destination directory (created if missing)
    - preserve_tree: if True, copy matched directories as subdirectories of dest_path;
                     if False, merge the contents of matched directories into dest_path.
    """
    if isinstance(src_patterns, (str, bytes)):
        src_patterns = [src_patterns]

    os.makedirs(dest_path, exist_ok=True)

    for pattern in src_patterns:
        matches = glob.glob(pattern, recursive=True)
        if not matches:
            logging.warning("No matches for pattern: %s", pattern)
            continue

        for src in matches:
            try:
                if os.path.isfile(src):
                    dest_file = os.path.join(dest_path, os.path.basename(src))
                    shutil.copy2(src, dest_file)
                    logging.info("Copied file %s → %s", src, dest_file)

                elif os.path.isdir(src):
                    if preserve_tree:
                        dest_subdir = os.path.join(dest_path, os.path.basename(src))
                        shutil.copytree(src, dest_subdir, dirs_exist_ok=True)
                        logging.info("Copied dir %s → %s", src, dest_subdir)
                    else:
                        # merge contents of src into dest_path, preserving subfolders
                        for root, _, files in os.walk(src):
                            rel = os.path.relpath(root, src)
                            target_root = dest_path if rel == "." else os.path.join(dest_path, rel)
                            os.makedirs(target_root, exist_ok=True)
                            for f in files:
                                src_file = os.path.join(root, f)
                                dest_file = os.path.join(target_root, f)
                                shutil.copy2(src_file, dest_file)
                                logging.info("Copied file %s → %s", src_file, dest_file)

                else:
                    logging.warning("Skipping unknown type: %s", src)

            except Exception:
                logging.exception("Error copying %s", src)


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
    commit_message = f"{PROJECT} config update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    run(f"git commit -m '{commit_message}' || echo 'No changes to commit'", cwd=REPO_PATH)
    run(f"git push {auth_url} {BRANCH}", cwd=REPO_PATH)
    logging.info("✅ Push completed successfully")


try:
    logging.info(f"=== Starting {PROJECT} config push ===")
    os.chdir(REPO_PATH)
    setup_git_identity()
    git_pull()
    copy_files('/etc/bind/*', f'{REPO_PATH}', preserve_tree=True)
    git_push()

except Exception as e:
    logging.error(f"❌ Error: {e}")
    print(f"Error: {e}")
else:
    logging.info("✅ Script finished successfully")

