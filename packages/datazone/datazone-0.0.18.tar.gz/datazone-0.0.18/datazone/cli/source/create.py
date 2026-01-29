import questionary
import typer
from rich import print

from datazone.cli.source.create_prompts import source_type_configuration_func_mapping
from datazone.core.common.types import SourceTypeHumanizedMap
from datazone.service_callers.crud import CrudServiceCaller


def create():
    _source_type = questionary.select("Select source type...", choices=SourceTypeHumanizedMap).unsafe_ask()
    name = typer.prompt("Source Name", type=str)

    source_type = SourceTypeHumanizedMap.get(_source_type)

    payload = {"name": name, "connection_parameters": {"source_type": source_type}}
    func = source_type_configuration_func_mapping[source_type]
    parameters = func()

    payload["connection_parameters"].update(parameters)

    CrudServiceCaller(entity_name="source").create_entity(
        payload=payload,
    )

    print("Source has created successfully :tada:")
