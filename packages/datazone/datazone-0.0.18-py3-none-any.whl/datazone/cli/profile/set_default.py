from datazone.core.common.settings import SettingsManager


def setdefault(profile_name: str):
    """
    Set the profile context
    """
    SettingsManager.set_default_profile(profile_name)
    print(f"Profile {profile_name} set as default")
