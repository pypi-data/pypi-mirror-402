from rich.console import Console
from rich.table import Table

from datazone.service_callers.crud import CrudServiceCaller

transaction_columns = [
    "ID",
    "Version",
    "Operation",
    "Mode",
    "Number Files",
    "Output Bytes",
    "Output Rows",
    "Transaction ID",
    "Timestamp",
]


def transactions(dataset_id: str, page_size: int = 20):
    response_data = CrudServiceCaller(entity_name="transaction").get_entity_list(
        params={"filters": f"[dataset.$id][$eq]:{dataset_id}", "page_size": page_size},
    )

    console = Console()

    table = Table(*transaction_columns)
    for datum in response_data.get("items"):
        values = [
            datum.get("id"),
            str(datum.get("version")),
            datum.get("operation"),
            datum.get("mode"),
            str(datum.get("operation_metrics").get("number_files")),
            str(datum.get("operation_metrics").get("number_output_bytes")),
            str(datum.get("operation_metrics").get("number_output_rows")),
            datum.get("transaction_id"),
            datum.get("timestamp"),
        ]
        table.add_row(*values)
    console.print(table)
