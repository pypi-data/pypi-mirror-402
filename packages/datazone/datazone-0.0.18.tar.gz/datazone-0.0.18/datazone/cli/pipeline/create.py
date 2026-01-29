import os

import typer
from rich import print

from datazone.core.common.config import ConfigReader


def create(
    name: str = typer.Option(..., prompt=True),
):
    path = f"{name}.py"

    if os.path.isfile(path):
        print(f"[bold red]Already you have a pipeline that named as {path}[/bold red]")
        return

    f = open(path, "w")
    f.close()

    config_file = ConfigReader()
    config_file.add_new_pipeline(path)

    print("[bold green]New pipeline has added.[/bold green] :tada:")
