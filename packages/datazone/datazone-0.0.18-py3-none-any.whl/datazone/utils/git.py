from typing import List, Dict

import git
from rich import print

from datazone.constants import Constants
from datazone.service_callers.crud import CrudServiceCaller
from datazone.service_callers.datazone import DatazoneServiceCaller


def initialize_git_repo(project_id: str) -> None:
    repository_session = CrudServiceCaller(
        entity_name="repository-session",
    ).create_entity(
        payload={"project": project_id},
    )
    token = repository_session.get("token")

    git_url = f"{DatazoneServiceCaller.get_service_url()}/git/{token}"

    repo = git.Repo.init()
    print("[green]Repository has initialized[/green]")

    origin = repo.create_remote("origin", git_url)

    origin.fetch()
    repo.git.checkout(Constants.DEFAULT_BRANCH_NAME)
    origin.pull()


def is_git_repo():
    try:
        _ = git.Repo()
    except git.exc.InvalidGitRepositoryError:
        return False
    else:
        return True


def has_origin() -> bool:
    repo = git.Repo()
    return len(repo.remotes) > 0


def check_origin_behind() -> List[Dict]:
    repo = git.Repo()

    # Fetch latest changes
    repo.remotes.origin.fetch()

    active_branch = repo.active_branch
    tracking_branch = active_branch.tracking_branch()

    if tracking_branch is None:
        raise ValueError(f"No tracking branch set for {active_branch.name}")

    # Get commits that are in tracking branch but not in local
    commits = []
    for commit in repo.iter_commits(f"{active_branch.name}..{tracking_branch.name}"):
        commits.append(
            {
                "hash": commit.hexsha[:8],
                "author": commit.author.name,
                "message": commit.message.strip(),
                "date": commit.committed_datetime.isoformat(),
            },
        )

    return commits


def get_pull_blocking_files() -> List[str]:
    repo = git.Repo()
    repo.remotes.origin.fetch()
    local_branch = repo.active_branch
    remote_branch = local_branch.tracking_branch()

    if not remote_branch:
        raise ValueError(f"No tracking branch set for {local_branch.name}")

    # Get files changed locally (modified + staged)
    local_changes: set[str] = {
        str(item.a_path) for item in repo.index.diff(None) if item.a_path
    }
    local_changes.update(
        str(item.a_path) for item in repo.index.diff("HEAD") if item.a_path
    )

    # Get files changed in remote
    remote_changes: set[str] = {
        str(item.a_path)
        for item in repo.index.diff(remote_branch.commit)
        if item.a_path
    }

    # Return files that have both local and remote changes
    return list(local_changes & remote_changes)
