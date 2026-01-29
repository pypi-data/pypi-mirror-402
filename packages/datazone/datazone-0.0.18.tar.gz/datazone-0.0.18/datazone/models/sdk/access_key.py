from pydantic import BaseModel


class AccessKey(BaseModel):
    id: str
    scope: str
    access_key_id: str
    secret_access_key: str
    expire_duration: str
