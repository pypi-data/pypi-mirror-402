from enum import Enum


class SourceType(str, Enum):
    MYSQL = "mysql"
    AWS_S3_CSV = "aws_s3_csv"
    POSTGRESQL = "postgresql"
    SAP_HANA = "sap_hana"
    AZURE_BLOB_STORAGE = "azure_blob_storage"
    MSSQL = "mssql"
    MONGODB = "mongodb"


SourceTypeHumanizedMap = {
    "MySQL": SourceType.MYSQL,
    "AWS S3 CSV": SourceType.AWS_S3_CSV,
    "PostgreSQL": SourceType.POSTGRESQL,
    "SAP HANA": SourceType.SAP_HANA,
    "Azure Blob Storage": SourceType.AZURE_BLOB_STORAGE,
    "MSSQL": SourceType.MSSQL,
    "MongoDB": SourceType.MONGODB,
}


class ExtractMode(str, Enum):
    OVERWRITE = "overwrite"
    APPEND = "append"
