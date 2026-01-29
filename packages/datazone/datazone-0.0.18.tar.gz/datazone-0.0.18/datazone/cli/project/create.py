from datazone.service_callers.crud import CrudServiceCaller
from rich import print
from datazone.utils import git as git_utils
from datazone.utils.helpers import create_path


def create(project_name: str) -> None:
    """
    Create new project. If project with the same name exists, it will be truncated.
    Args:
        project_name: Project name
    """
    create_path(path_name=project_name, change_directory=True)

    project = CrudServiceCaller(entity_name="project").create_entity(
        payload={"name": project_name},
    )
    git_utils.initialize_git_repo(project_id=project["id"])

    print(f":point_right: [blue]Go to repository directory: cd {project_name}/[/blue]")
