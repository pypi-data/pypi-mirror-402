from rich.console import Console
from rich.table import Table, Column

from datazone.service_callers.crud import CrudServiceCaller
from datazone.utils.helpers import get_created_by


def list_func(page_size: int = 20):
    response_data = CrudServiceCaller(entity_name="extract").get_entity_list(
        params={"page_size": page_size, "fetch_links": True},
    )

    console = Console()

    table = Table(
        Column("ID", width=24),
        "Name",
        Column("Source ID", width=24),
        Column("Project ID", width=24),
        Column("Dataset ID", width=24),
        "Mode",
        "Deploy Status",
        "Created At",
        "Created By",
    )
    for datum in response_data.get("items"):
        values = [
            datum.get("id"),
            datum.get("name"),
            datum.get("source").get("id"),
            datum.get("project").get("id") if datum.get("project") else "-",
            datum.get("dataset").get("id") if datum.get("dataset") else "-",
            datum.get("mode"),
            datum.get("deploy_status"),
            datum.get("created_at"),
            get_created_by(datum),
        ]
        table.add_row(*values)
    console.print(table)
