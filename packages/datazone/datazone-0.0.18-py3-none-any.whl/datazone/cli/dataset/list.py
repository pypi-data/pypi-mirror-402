from rich.console import Console
from rich.table import Table, Column

from datazone.service_callers.crud import CrudServiceCaller


def list_func(page_size: int = 20):
    response_data = CrudServiceCaller(entity_name="dataset").get_entity_list(
        params={"page_size": page_size},
    )

    console = Console()

    table = Table(Column(header="ID", width=24), "Name", "Alias", "Status", "Source", "Created At")
    items = response_data.get("items")
    if len(items) == 0:
        console.print("[bold orange]Not created any dataset yet[/bold orange]")
        return

    for datum in items:
        values = [
            datum.get("id"),
            datum.get("name"),
            datum.get("alias") or "-",
            datum.get("status") or "-",
            datum.get("source") or "-",
            datum.get("created_at"),
        ]
        table.add_row(*values)
    console.print(table)
