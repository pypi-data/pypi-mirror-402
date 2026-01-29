from os import environ as env

from datetime import datetime
from typing import Dict, Optional

from pydantic import BaseModel


class Profile(BaseModel):
    api_key: str
    server_endpoint: str
    is_default: Optional[bool] = False
    last_login: Optional[datetime] = None

    @staticmethod
    def __get_service_prefix() -> str:
        prefix = env.get("CUSTOM_SERVICE_PREFIX")
        return prefix if prefix is not None else "/api/v1"

    def get_service_url(self) -> str:
        return f"{self.server_endpoint}{self.__get_service_prefix()}"


class Settings(BaseModel):
    profiles: Dict[str, Profile] = {}
