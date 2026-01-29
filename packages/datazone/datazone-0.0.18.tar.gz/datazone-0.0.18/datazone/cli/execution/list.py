from typing import Optional, Dict

from rich.console import Console
from rich.table import Table, Column

from datazone.service_callers.crud import CrudServiceCaller
from datazone.utils.helpers import get_created_by


def list_func(pipeline_id: Optional[str] = None, extract_id: Optional[str] = None, page_size: int = 20) -> None:
    params: Dict = {"page_size": page_size}
    if pipeline_id is not None:
        params.update({"filters": f"[pipeline.$id][$eq]:{pipeline_id}"})
    elif extract_id is not None:
        params.update({"filters": f"[extract.$id][$eq]:{extract_id}"})

    response_data = CrudServiceCaller(entity_name="execution").get_entity_list(params=params)

    console = Console()

    table = Table(
        Column("ID", width=24),
        "Entity Type",
        Column("Entity ID", width=24),
        "Created At",
        "Started At",
        "Finished At",
        "Created By",
        "Status",
    )
    for datum in reversed(response_data.get("items")):
        values = [
            datum.get("id"),
            "Extract" if datum.get("extract") is not None else "Pipeline",
            datum.get("pipeline").get("id") if datum.get("pipeline") is not None else datum.get("extract").get("id"),
            datum.get("created_at"),
            datum.get("start_datetime"),
            datum.get("finish_datetime"),
            get_created_by(datum),
            datum.get("status"),
        ]
        table.add_row(*values)
    console.print(table)
