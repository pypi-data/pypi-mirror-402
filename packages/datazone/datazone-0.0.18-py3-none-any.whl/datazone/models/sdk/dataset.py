from datetime import datetime

from pydantic import BaseModel

from datazone.models.sdk.user import User


class DatasetProject(BaseModel):
    id: str
    name: str


class Dataset(BaseModel):
    id: str
    created_at: datetime | None = None
    created_by: User | None = None
    updated_at: datetime | None = None
    updated_by: User | None = None
    name: str
    alias: str
    description: str | None = None
    project: DatasetProject
    origin_type: str
    origin_metadata: dict | None = None
    storage_path: str
    status: str
    partition_by: dict | None = None
    last_transaction_date: str
    has_table: bool
    type: str
    is_usable_by_orion: bool
    orion_extra_prompt: str | None = None
