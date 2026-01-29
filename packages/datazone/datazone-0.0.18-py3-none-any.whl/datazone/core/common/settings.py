from pathlib import Path

from fernet import Fernet
import toml

from datazone.context import profile_context
from datazone.errors.common import DatazoneProfileNotFoundError
from datazone.models.settings import Settings, Profile
from datazone.utils.helpers import get_datazone_path


class SettingsManager:
    @staticmethod
    def get_settings_path():
        datazone_path = get_datazone_path()
        return datazone_path / "settings.toml"

    @staticmethod
    def get_key_path() -> Path:
        datazone_path = get_datazone_path()
        return datazone_path / "crypto_key"

    @classmethod
    def create_crypto_key(cls):
        fernet_key = Fernet.generate_key()
        key_path = cls.get_key_path()

        with open(key_path, "wb") as file:
            file.write(fernet_key)

    @classmethod
    def get_crypto_key(cls):
        key_path = cls.get_key_path()
        if not key_path.exists():
            cls.create_crypto_key()

        with open(key_path, "rb") as file:
            return file.read()

    @classmethod
    def create_initial_settings(cls):
        datazone_path = get_datazone_path()
        settings_file_path = cls.get_settings_path()

        if not datazone_path.exists():
            datazone_path.mkdir()

        if settings_file_path.exists():
            return

        with open(settings_file_path, "w+") as file:
            toml.dump({}, file)

    @classmethod
    def get_settings(cls) -> Settings:
        settings_file_path = cls.get_settings_path()

        if not settings_file_path.exists():
            cls.create_initial_settings()

        with open(settings_file_path, "r") as file:
            settings = toml.load(file)
            return Settings(**settings)

    @classmethod
    def ensure_profile_name(cls) -> str:
        """
        Get the profile name from the context or the first profile name in the settings.
        If there is no profile created yet, raise an error
        Returns:
            str: profile name
        Raises:
            DatazoneProfileNotFoundError: If there is no profile created yet
        """
        profile_name = profile_context.get()
        settings = cls.get_settings()
        if profile_name is None:
            # check default profile
            profile_name = next((name for name, profile in settings.profiles.items() if profile.is_default), None)
            if profile_name is None:
                # check first profile
                profile_name = next(iter(settings.profiles.keys()), None)
                if profile_name is None:
                    raise DatazoneProfileNotFoundError(detail="There is no profile created yet")
        else:
            if profile_name not in settings.profiles.keys():
                raise DatazoneProfileNotFoundError(detail=f"Profile {profile_name} not found")
        return profile_name

    @classmethod
    def set_default_profile(cls, profile_name: str):
        settings = cls.get_settings()
        if profile_name not in settings.profiles.keys():
            raise DatazoneProfileNotFoundError(detail=f"Profile {profile_name} not found")

        for name, profile in settings.profiles.items():
            profile.is_default = name == profile_name
        settings_file_path = cls.get_settings_path()
        with open(settings_file_path, "w") as file:
            toml.dump(settings.dict(), file)

    @classmethod
    def get_profile(cls, profile_name: str | None = None) -> Profile:
        settings = cls.get_settings()
        if profile_name is None:
            profile_name = cls.ensure_profile_name()
        profile = settings.profiles[profile_name]
        return profile

    @classmethod
    def check_profile_exists(cls, profile_name: str) -> bool:
        settings = cls.get_settings()
        return profile_name in settings.profiles

    @classmethod
    def delete_profile(cls, profile_name: str):
        settings = cls.get_settings()
        if profile_name not in settings.profiles:
            raise DatazoneProfileNotFoundError(detail=f"Profile {profile_name} not found")
        settings.profiles.pop(profile_name)
        settings_file_path = cls.get_settings_path()
        with open(settings_file_path, "w") as file:
            toml.dump(settings.dict(), file)

    @classmethod
    def create_profile(cls, profile_name: str, api_key: str, server_endpoint: str):
        settings = cls.get_settings()
        profile = Profile(api_key=api_key, server_endpoint=server_endpoint)
        settings.profiles[profile_name] = profile
        settings_file_path = cls.get_settings_path()
        with open(settings_file_path, "w") as file:
            toml.dump(settings.dict(), file)
        cls.set_default_profile(profile_name)
