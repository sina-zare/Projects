import os
from git import Repo
import jdatetime
from datetime import datetime, timedelta, timezone


def git_commit_and_push(repo_path, commit_message, git_url, local_branch="master", remote_branch="main"):
    try:
        # Check if the repo exists, if not initialize and set remote
        if not os.path.exists(repo_path):
            print(f"Initializing new repository at {repo_path}...")
            os.makedirs(repo_path)  # Make the directory if it doesn't exist
            repo = Repo.init(repo_path)  # Initialize the repo
            origin = repo.create_remote('origin', git_url)  # Set remote URL
        else:
            # Use the existing repository
            repo = Repo(repo_path)

        # Fetch the latest changes from the remote
        print(f"Fetching latest changes from {remote_branch}...")
        origin = repo.remote(name='origin')
        origin.fetch()

        # Pull the changes from the remote branch into the local branch, allowing unrelated histories
        print(f"Pulling changes from {remote_branch}...")
        repo.git.pull('origin', remote_branch, '--allow-unrelated-histories')

        # Check if there are any changes to commit
        if repo.is_dirty() or not repo.head.is_valid():
            # Stage an initial file or use an empty commit to create the first commit
            # For example, create an empty file
            with open(os.path.join(repo_path, "initial_commit.txt"), "w") as f:
                f.write("Initial commit.")
            repo.git.add(A=True)
            repo.index.commit("Initial commit")
            print(f"Initial commit created.")

        # Stage all changes
        repo.git.add(A=True)

        # Commit changes
        repo.index.commit(commit_message)
        print(f"Committed changes with message: {commit_message}")

        # Set the upstream for the branch (ensure pushing from local to remote)
        if repo.head.ref.name == local_branch:
            origin.push(f"{local_branch}:{remote_branch}")
            print(f"Pushed changes from {local_branch} to remote {remote_branch}")
        else:
            repo.git.push("--set-upstream", "origin", f"{local_branch}:{remote_branch}")
            print(f"Set upstream and pushed changes from {local_branch} to remote {remote_branch}")
    #except GitCommandError as e:
    #    print(f"Git error occurred: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")


# Replace with your GitLab repository URL with access token
# Use this format: https://<username>:<access-token>@gitlab.com/<namespace>/<repository>.git
git_url = "https://xyz:xyz@me-gitlab.abramad.com/operation/sysops/zabbix.git"

# Path to your local repository
repo_path = "C:\\Gitlab"



# Get current time in UTC with timezone-aware object
now_utc = datetime.now(timezone.utc)
# Apply the +3:30 timezone offset
time_with_offset = now_utc + timedelta(hours=3, minutes=30)
# Convert to Jalali
jalali_time = jdatetime.datetime.fromgregorian(datetime=time_with_offset)
# Format to remove milliseconds
formatted_jalali_time = jalali_time.strftime('%Y-%m-%d %H:%M:%S')


# Commit message
commit_message = f"script uploaded new files at {formatted_jalali_time}"

# Call the function
git_commit_and_push(repo_path, commit_message, git_url, local_branch="master", remote_branch="main")
