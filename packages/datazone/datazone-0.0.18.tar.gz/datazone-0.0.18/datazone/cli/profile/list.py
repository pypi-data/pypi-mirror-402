from rich.console import Console
from rich.table import Table

from datazone.core.common.settings import SettingsManager

columns = [
    "Name",
    "Host",
    "API Key",
    "Default",
]


def list_func():
    settings = SettingsManager.get_settings()

    console = Console()

    table = Table(*columns)
    for name, profile in settings.profiles.items():
        values = [
            name,
            profile.server_endpoint,
            profile.api_key[:8] + "****",
            "Yes" if profile.is_default else "No",
        ]
        table.add_row(*values)
    console.print(table)
