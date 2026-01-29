from rich.console import Console
from rich.table import Table, Column

from datazone.models.service_models import ProjectListModel
from datazone.service_callers.crud import CrudServiceCaller


def list_func(page_size: int = 20):
    response_data = CrudServiceCaller(entity_name="project").get_entity_list(
        params={"page_size": page_size, "fetch_links": "true"},
    )
    console = Console()

    table = Table(Column("ID", width=24), "Name", "Created At", "Created By")
    for datum in response_data.get("items"):
        project = ProjectListModel(**datum)

        values = [
            project.id,
            project.name,
            project.created_at,
            project.created_by.full_name if project.created_by else "-",
        ]
        table.add_row(*values)
    console.print(table)
