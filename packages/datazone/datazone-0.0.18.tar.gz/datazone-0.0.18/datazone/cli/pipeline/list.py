from rich.console import Console
from rich.table import Table, Column

from datazone.service_callers.crud import CrudServiceCaller
from datazone.utils.helpers import get_created_by


def list_func(page_size: int = 20):
    response_data = CrudServiceCaller(entity_name="pipeline").get_entity_list(
        params={"page_size": page_size, "fetch_links": True},
    )

    console = Console()

    table = Table(
        Column("ID", width=24),
        "Name",
        Column("Project ID", width=24),
        "Created At",
        "Created By",
    )
    for datum in response_data.get("items"):
        values = [
            datum.get("id"),
            datum.get("name"),
            datum.get("project").get("id") if datum.get("project") else "-",
            datum.get("created_at"),
            get_created_by(datum),
        ]
        table.add_row(*values)
    console.print(table)
