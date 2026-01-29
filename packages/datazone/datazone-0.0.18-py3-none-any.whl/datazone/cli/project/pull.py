import git
from rich import print

from datazone.utils.git import get_pull_blocking_files
from datazone.utils.helpers import check_datazone_repo


def pull() -> None:
    check_datazone_repo()
    files = get_pull_blocking_files()
    if len(files) > 0:
        print(
            """[bold red]There are modified files that are blocking the pull operation."""
            """Please commit or stash your local changes.[/bold red]""",
        )
        for file in files:
            print("[red]File:[/red] ", file)
        return

    repo = git.Repo()
    origin = repo.remotes.origin

    origin.pull(ff_only=True)
    print("[green]Repository is up to date.[/green]:rocket:")
