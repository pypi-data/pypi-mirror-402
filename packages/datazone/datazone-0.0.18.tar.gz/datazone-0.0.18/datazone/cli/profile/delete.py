from datazone.core.common.settings import SettingsManager


def delete(profile_name: str):
    """
    Delete a profile
    """
    SettingsManager.delete_profile(profile_name)
    print(f"Profile {profile_name} deleted")
