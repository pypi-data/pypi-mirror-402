from datetime import datetime
from typing import List

from pydantic import BaseModel

from datazone.models.sdk.common import MongoRefField


class Project(BaseModel):
    config_file_content: dict | None = None
    cover_image: dict | None = None
    deploy_status: str
    description: str | None = None
    id: str
    is_deleted: bool
    last_load_at: datetime | None = None
    name: str
    organisation: MongoRefField
    repository_name: str
    settings: dict | None = None
    tags: List[MongoRefField] | None = None

    created_at: datetime | None = None
    created_by: MongoRefField | None = None
    updated_at: datetime | None = None
    updated_by: MongoRefField | None = None
