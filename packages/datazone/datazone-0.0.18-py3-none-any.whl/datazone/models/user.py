from pydantic import BaseModel

from datazone.utils.types import PydanticObjectId


class User(BaseModel):
    id: PydanticObjectId
    email: str
    full_name: str
