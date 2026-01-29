from typing import Dict

import questionary
import typer
from rich import print

from datazone.cli.extract.create_prompts import source_type_parameter_func_mapping
from datazone.core.common.types import ExtractMode
from datazone.service_callers.crud import CrudServiceCaller


def check_source(source_id: str) -> Dict:
    print("[bold blue]Checking source instance...[/bold blue]")
    source = CrudServiceCaller(entity_name="source").get_entity_with_id(entity_id=source_id)
    return source


def create():
    sources = CrudServiceCaller(entity_name="source").get_entity_list()
    if len(sources.get("items")) == 0:
        print("[bold yellow]There is no source to create extract. Please create a source first.[/bold yellow]")
        return

    source_names = {f"{source['name']} - {source['id']}": source["id"] for source in sources.get("items")}
    _source = questionary.select("Select source...", choices=source_names).unsafe_ask()

    name = typer.prompt("Extract Name", type=str)
    mode: ExtractMode = questionary.select(
        "Extract Mode...", choices=[ExtractMode.OVERWRITE, ExtractMode.APPEND],
    ).unsafe_ask()

    selected_source = source_names.get(_source)
    selected_source_dict = next((source for source in sources.get("items") if source["id"] == selected_source))
    source_type = selected_source_dict.get("connection_parameters").get("source_type")

    func = source_type_parameter_func_mapping[source_type]
    payload = {
        "name": name,
        "mode": mode,
        "source": selected_source,
    }
    parameters = func(mode=mode)
    payload["source_parameters"] = parameters
    CrudServiceCaller(entity_name="extract").create_entity(payload=payload)

    print("[bold green]Extract has created successfully [/bold green] :tada:")
