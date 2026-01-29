import os
import shutil
from pathlib import Path
from typing import Dict

import typer

from datazone.core.common.config import ConfigReader
from datazone.errors.common import InvalidRepositoryError


def create_path(path_name: str, change_directory: bool = False) -> None:
    path = Path(path_name)
    if path.exists():
        delete = typer.confirm(
            f"There is {path} folder, it will be truncated. Are you sure?",
        )
        if not delete:
            return

        shutil.rmtree(path)

    os.mkdir(path)
    if change_directory:
        os.chdir(path)


def get_datazone_path() -> Path:
    return Path.home() / ".datazone"


def check_host_https(host: str) -> str:
    """
    Check if host starts with https:// or http://, if not, add https:// to the beginning of the host.
    Args:
        host (str): host name
    Returns:
        str: host name with https:// at the beginning
    """
    if not host.startswith("https://") and not host.startswith("http://"):
        return f"https://{host}"
    return host


def check_datazone_repo() -> bool:
    """
    Check if the current directory is a datazone repository.
    Returns:
        bool: True if the current directory is a datazone repository, False otherwise.
    """
    from datazone.utils.git import is_git_repo, has_origin

    if not is_git_repo() or not has_origin():
        raise InvalidRepositoryError

    config_file = ConfigReader()
    config_file.read_config_file()
    return True


def get_created_by(payload: Dict) -> str:
    user_data = payload.get("created_by")
    if user_data:
        return user_data.get("email", "-")
    return "-"


def ensure_http(url: str) -> str:
    """
    Ensure that the URL starts with http:// or https://.
    Args:
        url (str): URL to check
    Returns:
        str: URL with http:// or https:// at the beginning
    """
    if url.startswith("https://"):
        url = url.replace("https://", "http://", 1)
    elif not url.startswith("http://"):
        url = f"http://{url}"
    return url
