from typing import Dict, Callable

import typer

from datazone.core.common.types import SourceType, ExtractMode


def common_db_parameters(mode: ExtractMode) -> Dict:
    table_name: str = typer.prompt("Table Name")
    parameters = {"table_name": table_name}

    if mode == ExtractMode.APPEND:
        replication_key = typer.prompt("Replication Key", type=str, default="id")
        parameters.update({"replication_key": replication_key})

    return parameters


def aws_s3_csv_source_parameters(mode: ExtractMode) -> Dict:
    search_prefix: str = typer.prompt("Search Prefix", default="/")
    search_pattern: str = typer.prompt("Search Pattern", default=".*\\.csv")

    return {"search_prefix": search_prefix, "search_pattern": search_pattern}


def azure_blob_storage_source_parameters(mode: ExtractMode) -> Dict:
    blob_directory: str = typer.prompt("Blob Directory")
    return {"blob_directory": blob_directory}


def mongo_db_source_parameters(mode: ExtractMode) -> Dict:
    collection_name: str = typer.prompt("Collection Name")
    parameters = {"collection_name": collection_name}
    if mode == ExtractMode.APPEND:
        replication_key = typer.prompt("Replication Key", type=str, default="id")
        parameters.update({"replication_key": replication_key})
    return parameters


source_type_parameter_func_mapping: Dict[SourceType, Callable[[ExtractMode], Dict]] = {
    SourceType.MYSQL: common_db_parameters,
    SourceType.AWS_S3_CSV: aws_s3_csv_source_parameters,
    SourceType.POSTGRESQL: common_db_parameters,
    SourceType.SAP_HANA: common_db_parameters,
    SourceType.AZURE_BLOB_STORAGE: azure_blob_storage_source_parameters,
    SourceType.MSSQL: common_db_parameters,
    SourceType.MONGODB: mongo_db_source_parameters,
}
