from typing import Dict

import typer

from datazone.core.common.types import SourceType


def mysql_source_configurations() -> Dict:
    host = typer.prompt("Host", type=str)
    port = typer.prompt("Port", type=str, default="3306")
    user = typer.prompt("User", type=str)
    password = typer.prompt("Password", hide_input=True, confirmation_prompt=True, type=str)
    database_name = typer.prompt("Database Name", type=str)
    schema_name = typer.prompt("Schema Name", type=str, default="None")

    # We can't set None value as default, so we are forced to that hackish method.
    schema_name = None if schema_name == "None" else schema_name

    return {
        "host": host,
        "port": port,
        "user": user,
        "password": password,
        "database_name": database_name,
        "schema_name": schema_name,
    }


def aws_s3_csv_source_configurations() -> Dict:
    bucket_name: str = typer.prompt("Bucket Name")
    aws_access_key_id: str = typer.prompt("AWS Access Key ID")
    aws_secret_access_key: str = typer.prompt("AWS Secret Access Key", hide_input=True)

    return {
        "bucket_name": bucket_name,
        "aws_access_key_id": aws_access_key_id,
        "aws_secret_access_key": aws_secret_access_key,
    }


def postgresql_source_configurations() -> Dict:
    host = typer.prompt("Host", type=str)
    port = typer.prompt("Port", type=str, default="5432")
    user = typer.prompt("User", type=str)
    password = typer.prompt("Password", hide_input=True, confirmation_prompt=True, type=str)
    database_name = typer.prompt("Database Name", type=str)
    schema_name = typer.prompt("Schema Name", type=str, default="None")

    # We can't set None value as default, so we are forced to that hackish method.
    schema_name = None if schema_name == "None" else schema_name

    return {
        "host": host,
        "port": port,
        "user": user,
        "password": password,
        "database_name": database_name,
        "schema_name": schema_name,
    }


def sap_hana_source_configurations() -> Dict:
    host = typer.prompt("Host", type=str)
    port = typer.prompt("Port", type=str)
    user = typer.prompt("User", type=str)
    password = typer.prompt("Password", hide_input=True, confirmation_prompt=True, type=str)

    return {
        "host": host,
        "port": port,
        "user": user,
        "password": password,
    }


def azure_blob_storage_source_configurations() -> Dict:
    account_url = typer.prompt("Account URL", type=str)
    token = typer.prompt("Token", type=str)
    container_name = typer.prompt("Container Name", type=str)

    return {
        "account_url": account_url,
        "token": token,
        "container_name": container_name,
    }


def mssql_source_configurations() -> Dict:
    host = typer.prompt("Host", type=str)
    port = typer.prompt("Port", type=str, default="1433")
    user = typer.prompt("User", type=str)
    password = typer.prompt("Password", hide_input=True, confirmation_prompt=True, type=str)
    database_name = typer.prompt("Database Name", type=str)
    schema_name = typer.prompt("Schema Name", type=str, default="None")

    # We can't set None value as default, so we are forced to that hackish method.
    schema_name = None if schema_name == "None" else schema_name

    return {
        "host": host,
        "port": port,
        "user": user,
        "password": password,
        "database_name": database_name,
        "schema_name": schema_name,
    }


def mongodb_source_configurations() -> Dict:
    host = typer.prompt("Host", type=str)
    port = typer.prompt("Port", type=str, default="27017")
    user = typer.prompt("User", type=str)
    password = typer.prompt("Password", hide_input=True, confirmation_prompt=True, type=str)
    database_name = typer.prompt("Database Name", type=str)

    return {
        "host": host,
        "port": port,
        "user": user,
        "password": password,
        "database_name": database_name,
    }


source_type_configuration_func_mapping = {
    SourceType.MYSQL: mysql_source_configurations,
    SourceType.AWS_S3_CSV: aws_s3_csv_source_configurations,
    SourceType.POSTGRESQL: postgresql_source_configurations,
    SourceType.SAP_HANA: sap_hana_source_configurations,
    SourceType.AZURE_BLOB_STORAGE: azure_blob_storage_source_configurations,
    SourceType.MSSQL: mssql_source_configurations,
    SourceType.MONGODB: mongodb_source_configurations,
}
