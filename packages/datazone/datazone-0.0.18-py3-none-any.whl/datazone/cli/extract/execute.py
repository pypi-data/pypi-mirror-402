from rich import print

from datazone.cli.execution.log import log
from datazone.service_callers.datazone import DatazoneServiceCaller


def execute(extract_id: str) -> None:
    """
    Start execution for extract
    """
    response_data = DatazoneServiceCaller.run_execution_extract(extract_id=extract_id)

    _id = response_data.get("id")
    print(f"[bold blue]Execute ID: {_id}[/bold blue]")

    log(execution_id=_id)
