from typing import Optional

from rich.console import Console
from rich.table import Table

from datazone.core.common.config import ConfigReader
from datazone.models.config import Config
from datazone.service_callers.datazone import DatazoneServiceCaller

columns = [
    "Pipeline ID",
    "Pipeline Name",
    "Deploy Status",
    "Transform Name",
    "Function Name",
    "Output Name",
    "Materialized",
    "Dataset ID",
]


def get_repository_id_from_config_file() -> str:
    """It reads config yaml file in current directory and returns."""
    config_file = ConfigReader()

    config: Config = config_file.read_config_file()

    repository_id = str(config.project_id)
    return repository_id


def summary(repository_id: Optional[str] = None) -> None:
    """
    Get summary about project
    """
    if repository_id is None:
        repository_id = get_repository_id_from_config_file()

    response_data = DatazoneServiceCaller.get_project_summary(project_id=repository_id)

    pipelines = response_data["pipelines"]

    rows = []
    for pipeline in pipelines:
        transforms = pipeline.get("transforms")
        for transform in transforms:
            outputs = transform.get("outputs")
            for output in outputs:
                rows.append(
                    [
                        pipeline["pipeline"]["id"],
                        pipeline["pipeline"]["name"],
                        pipeline["pipeline"]["deploy_status"],
                        transform["transform"]["name"],
                        transform["transform"]["function_name"],
                        output["name"],
                        str(output["materialized"]),
                        output.get("dataset").get("id") if output.get("dataset") else "",
                    ],
                )

    console = Console()

    table = Table(*columns)
    for row in rows:
        table.add_row(*row)
    console.print(table)
