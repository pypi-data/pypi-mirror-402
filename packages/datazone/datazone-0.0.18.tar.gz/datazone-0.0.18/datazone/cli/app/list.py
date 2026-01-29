from typing import Optional, Dict, Any

import typer
from rich.console import Console
from rich.table import Table, Column

from datazone.service_callers.crud import CrudServiceCaller
from datazone.utils.helpers import get_created_by


def list_func(
    page_size: int = 20,
    project_id: Optional[str] = typer.Option(None, help="Filter by project id"),
):
    params: Dict[str, Any] = {"page_size": page_size, "fetch_links": True}
    if project_id:
        params["filters"] = f"[project.$id][$eq]:{project_id}"

    response_data = CrudServiceCaller(entity_name="intelligent-app").get_entity_list(
        params=params,
    )

    console = Console()

    table = Table(
        Column("ID", width=24),
        "Name",
        Column("Project ID", width=24),
        "Description",
        "Created At",
        "Created By",
    )
    items = response_data.get("items")
    if not items or len(items) == 0:
        console.print("[bold orange]Not created any intelligent app yet[/bold orange]")
        return

    for datum in items:
        project = datum.get("project")
        project_id_val = (
            (project.get("id") if isinstance(project, dict) else project)
            if project
            else "-"
        )

        app_def = datum.get("app_definition", {})
        name = app_def.get("name", "-") if app_def else "-"
        description = app_def.get("description", "-") if app_def else "-"

        if description and len(description) > 50:
            description = description[:47] + "..."

        values = [
            datum.get("id"),
            name,
            project_id_val,
            description or "-",
            datum.get("created_at"),
            get_created_by(datum),
        ]
        table.add_row(*values)
    console.print(table)
