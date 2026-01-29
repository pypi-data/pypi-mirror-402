import requests
from datazone.core.common.settings import SettingsManager
from datazone.errors.auth import DatazoneInvalidGrantError


class AuthService:
    @staticmethod
    def check_session(profile_name: str | None = None) -> dict[str, str]:
        profile = SettingsManager.get_profile(profile_name)
        response = requests.get(
            f"{profile.get_service_url()}/user/me",
            headers={"x-api-key": profile.api_key},
        )

        if not response.ok:
            raise DatazoneInvalidGrantError(detail="Invalid api key!")

        user_data = response.json()
        return user_data

    @classmethod
    def get_session(cls, profile_name: str | None = None) -> requests.Session:
        cls.check_session(profile_name)

        profile = SettingsManager.get_profile()
        session = requests.Session()
        session.headers.update({"x-api-key": profile.api_key})
        return session
