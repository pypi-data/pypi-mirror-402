from pathlib import Path

from rich import print

from datazone.cli.execution.run import run as run_execution
from datazone.cli.project.deploy import deploy
from datazone.core.common.config import ConfigReader
from datazone.service_callers.datazone import DatazoneServiceCaller


def run(file_path: Path) -> None:
    if not file_path.exists():
        print("[red]File not found![/red]")
        return

    config_file = ConfigReader()
    config = config_file.read_config_file()
    project_id = config.project_id

    pipeline = next((p for p in config.pipelines if p.path.absolute() == file_path.absolute()), None)

    if pipeline is None:
        print("[red]Specified file is not a pipeline![/red]")
        return

    deployed = deploy()
    if not deployed:
        return

    # TODO: move it to service caller module
    session = DatazoneServiceCaller.get_session()
    response = session.get(
        f"{DatazoneServiceCaller.get_service_url()}/pipeline/list"
        f"?filters=[alias][$eq]:{pipeline.alias}"
        f"&filters=[project.$id][$eq]:{project_id}",
    )
    response.raise_for_status()
    data = response.json()
    data = data.get("items")

    if data is None or len(data) == 0:
        print("[red]Pipeline not found![/red]")
        return

    pipeline_id = data[0]["id"]
    run_execution(pipeline_id=pipeline_id)
