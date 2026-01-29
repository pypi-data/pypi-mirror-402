from typing import Optional, Dict, Any

import typer
from rich.console import Console
from rich.table import Table, Column

from datazone.service_callers.crud import CrudServiceCaller
from datazone.utils.helpers import get_created_by

source_columns = [
    Column("ID", width=24),
    "Name",
    Column("Dataset ID", width=24),
    Column("Project ID", width=24),
    "Status",
    "Created At",
    "Created By",
]


def list_func(
    page_size: int = 20,
    dataset_id: Optional[str] = typer.Option(None, help="Filter by dataset id"),
):
    params: Dict[str, Any] = {"page_size": page_size, "fetch_links": True}
    if dataset_id:
        params["filters"] = f"[dataset.$id][$eq]:{dataset_id}"

    response_data = CrudServiceCaller(entity_name="view").get_entity_list(
        params=params,
    )

    console = Console()

    table = Table(
        Column("ID", width=24),
        "Name",
        Column("Dataset ID", width=24),
        Column("Project ID", width=24),
        "Status",
        "Created At",
        "Created By",
    )
    items = response_data.get("items")
    if not items or len(items) == 0:
        console.print("[bold orange]Not created any view yet[/bold orange]")
        return

    for datum in items:
        dataset = datum.get("dataset")
        dataset_id_val = dataset.get("id") if dataset else "-"
        project = datum.get("project")
        project_id_val = (project.get("id") if isinstance(project, dict) else project) if project else "-"
        values = [
            datum.get("id"),
            datum.get("name"),
            dataset_id_val,
            project_id_val,
            datum.get("status", "-"),
            datum.get("created_at"),
            get_created_by(datum),
        ]
        table.add_row(*values)
    console.print(table)
