from rich.console import Console
from rich.table import Table

from datazone.service_callers.crud import CrudServiceCaller
from datazone.utils.helpers import get_created_by

schedule_columns = ["ID", "Name", "Expression", "Extract ID", "Pipeline ID", "Active", "Created At", "Created By"]


def list_func(page_size: int = 20):
    response_data = CrudServiceCaller(entity_name="schedule").get_entity_list(
        params={"page_size": page_size},
    )
    console = Console()

    table = Table()
    table.add_column("ID", width=24)
    table.add_column("Name")
    table.add_column("Expression")
    table.add_column("Extract ID", width=24)
    table.add_column("Pipeline ID", width=24)
    table.add_column("Active")
    table.add_column("Created At")
    table.add_column("Created By")
    for datum in response_data.get("items"):
        values = [
            datum.get("id"),
            datum.get("name"),
            datum.get("expression"),
            datum.get("extract").get("id") if datum.get("extract") else None,
            datum.get("pipeline").get("id") if datum.get("pipeline") else None,
            str(datum.get("is_active")),
            datum.get("created_at"),
            get_created_by(datum),
        ]
        table.add_row(*values)
    console.print(table)
