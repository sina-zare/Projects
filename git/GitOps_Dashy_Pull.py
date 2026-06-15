#!/usr/bin/env python3
import os
import shutil
import subprocess
import logging
import sys
import glob

# --- Configuration ---
REPO_PATH = "/opt/scripts/pull-push-config/git-files"  # local working copy of the git repo
GITLAB_URL = "https://gitlab.abramad.com/abramad/sysops/dashy.git"
BRANCH = "main"
LOG_FILE = "/opt/scripts/pull-push-config/logs/logger_pull.log"

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


logging.info("=== Starting Dashy config pull ===")
try:
    ensure_repo()
    '''
    Compose file:
    /opt/compose-files/dashy/docker-compose.yml

    Config file:
    /opt/compose-files/dashy/user-data/conf.yml
    
    Image files:
    /opt/compose-files/dashy/user-data/item-icons/*
    '''
    try:
        copy_files([f"{REPO_PATH}/docker-compose.yml"], '/opt/compose-files/dashy')
        copy_files([f"{REPO_PATH}/user-data/conf.yml"], '/opt/compose-files/dashy/user-data')
        copy_files([f"{REPO_PATH}/user-data/item-icons/*"], '/opt/compose-files/dashy/user-data/item-icons')

        logging.info("✅ Successfully Pulled")
        print("✅ Successfully Pulled")

    except Exception as e:
        logging.error(f"❌ Error during apply: {e}")
        print(f"Error during apply: {e}")

except Exception as e:
    logging.error(f"❌ Error: {e}")
    print(f"❌ Error: {e}")
    sys.exit(1)
else:
    logging.info("✅ Script finished successfully")
    sys.exit(0)
