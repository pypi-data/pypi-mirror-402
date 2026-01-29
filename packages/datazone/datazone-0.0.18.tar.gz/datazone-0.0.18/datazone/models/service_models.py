from pydantic import BaseModel

from datazone.models.user import User


class ProjectListModel(BaseModel):
    id: str
    name: str
    created_at: str
    created_by: User | None = None
