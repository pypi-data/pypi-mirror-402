from abc import ABC

from datazone.core.common.settings import SettingsManager
from datazone.core.connections.auth import AuthService
from datazone.core.connections.session import adapter


class BaseServiceCaller(ABC):

    @classmethod
    def get_service_url(cls) -> str:
        profile = SettingsManager.get_profile()
        return profile.get_service_url()

    @classmethod
    def get_session(cls):
        session = AuthService.get_session()

        session.mount("https://", adapter=adapter)
        session.mount("http://", adapter=adapter)

        return session
