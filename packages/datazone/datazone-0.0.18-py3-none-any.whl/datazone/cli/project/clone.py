from rich import print

from datazone.service_callers.crud import CrudServiceCaller
from datazone.utils.helpers import create_path
from datazone.utils.git import initialize_git_repo


def clone(project_id: str) -> None:
    project = CrudServiceCaller(entity_name="project").get_entity_with_id(entity_id=project_id)
    print("[green]Project has fetched...[/green]:rocket:")

    project_name = project["name"]
    create_path(path_name=project_name, change_directory=True)

    initialize_git_repo(project_id=project["id"])

    print("[green]Repository is ready.[/green]:rocket:")
    print(f":point_right: [blue]Go to directory: cd {project_name}/[/blue]")
