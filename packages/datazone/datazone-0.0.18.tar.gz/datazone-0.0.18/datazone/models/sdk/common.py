from pydantic import BaseModel


class MongoRefField(BaseModel):
    collection: str
    id: str
