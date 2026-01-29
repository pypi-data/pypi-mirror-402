import typer
from rich.console import Console
from rich.table import Table

from datazone.service_callers.datazone import DatazoneServiceCaller


app = typer.Typer()

activity_columns = [
    "ID",
    "Project ID",
    "User",
    "Commit ID",
    "Commit Message",
    "Timestamp",
    "Deploy Status",
]


@app.command(name="list")
def list_func(project_id: str, page_size: int = 20) -> None:
    """List project deploy activities."""
    params = {"page_size": page_size}
    response_data = DatazoneServiceCaller.get_project_activities(project_id=project_id, params=params)

    console = Console()

    table = Table(*activity_columns)
    items = response_data.get("items")
    if not items or len(items) == 0:
        console.print("[bold orange]No activities yet[/bold orange]")
        return

    for datum in items:
        _id = datum.get("id") or datum.get("_id")
        project = datum.get("project") or {}
        project_id_val = project.get("id") or project.get("_id") or "-"
        values = [
            _id,
            project_id_val,
            datum.get("git_user", "-"),
            datum.get("commit_id", "-"),
            datum.get("commit_message", "-"),
            datum.get("timestamp", "-"),
            datum.get("deploy_status", "-"),
        ]
        table.add_row(*[str(v) for v in values])
    console.print(table)
