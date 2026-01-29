import uuid
from enum import Enum
from typing import Optional, List, Dict

import git
from rich import print
from rich.table import Table

from datazone.constants import Constants
from datazone.utils.git import check_origin_behind
from datazone.utils.helpers import check_datazone_repo


class ChangeType(str, Enum):
    MODIFIED = "modified"
    ADDED = "added"
    DELETED = "deleted"


def git_push_changes(commit_message: Optional[str] = None) -> None:
    """
    Push changes to the repository. If commit message is not provided, it will be generated automatically as uuid.
    Args:
        commit_message (Optional[str]): Optional commit message
    """
    commit_message = commit_message or str(uuid.uuid4())

    repo = git.Repo()
    origin = repo.remotes.origin

    origin.fetch()
    repo.git.checkout(Constants.DEFAULT_BRANCH_NAME)

    repo.git.add(A=True)  # This is equivalent to 'git add -A'

    # Remove all deleted files
    deleted_files = [
        item.a_path for item in repo.index.diff(None) if item.change_type == "D"
    ]
    if deleted_files:
        repo.index.remove(deleted_files, working_tree=True)

    repo.index.commit(commit_message)
    origin.push(Constants.DEFAULT_BRANCH_NAME)
    print("[green]Files have pushed to the repository.[/green]:rocket:")


def get_changed_files_and_content() -> List[Dict]:
    """
    Get changed files and content.
    Returns:
        List[Dict]: List of changed files and content
    """
    repo = git.Repo()
    modified_files: List[str] = [
        item.a_path
        for item in repo.index.diff(None)
        if item.change_type != "D" and item.a_path
    ]
    deleted_files = [
        item.a_path
        for item in repo.index.diff(None)
        if item.change_type == "D" and item.a_path
    ]

    added_files: List[str] = [
        item.a_path for item in repo.index.diff("HEAD") if item.a_path
    ]
    untracked_files = repo.untracked_files
    added_files.extend(untracked_files)

    changed_content = []
    for file_path in modified_files:
        with open(file_path, "r") as f:
            changed_content.append(
                {
                    "file_name": file_path,
                    "content": f.read(),
                    "change_type": ChangeType.MODIFIED,
                },
            )

    for file_path in added_files:
        with open(file_path, "r") as f:
            changed_content.append(
                {
                    "file_name": file_path,
                    "content": f.read(),
                    "change_type": ChangeType.ADDED,
                },
            )

    for file in deleted_files:
        changed_content.append({"file_name": file, "change_type": ChangeType.DELETED})

    return changed_content


def deploy(
    file: Optional[str] = None, commit_message: Optional[str] = None,
) -> bool | None:
    """
    Deploy project to the repository.
    Args:
        file: path to the custom config file
        commit_message: commit message
    """
    check_datazone_repo()

    origin_commits = check_origin_behind()
    if origin_commits:
        table = Table(*["hash", "author", "message", "date"])
        for datum in origin_commits[:5]:
            table.add_row(*datum.values())
        print(table)
        print(
            "[bold red]There are commits in the origin that are not in the local repository.[/bold red]",
        )
        print(
            "[bold red]You can pull the changes with `datazone project pull` command.[/bold red]",
        )
        return False

    print("[bold green]Deploying...[/bold green]")
    git_push_changes(commit_message)
    return True
