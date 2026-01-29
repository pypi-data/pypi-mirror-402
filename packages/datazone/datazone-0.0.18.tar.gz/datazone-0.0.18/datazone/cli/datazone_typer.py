from typing import Type
from os import environ as env

from requests import HTTPError
from rich import print

import typer

from datazone.errors.base import DatazoneError

DatazoneExceptionType = Type[DatazoneError]

debug_mode = env.get("DEBUG", "false") == "true"


class DatazoneTyper(typer.Typer):
    @staticmethod
    def handle_datazone_error(exc: DatazoneExceptionType):
        from rich import print

        error_message = f":warning: [bold red]{exc.message}[/bold red]"

        if hasattr(exc, "detail") and getattr(exc, "detail") is not None:
            error_message += f" - Exception Detail: {exc.detail}"
        print(error_message)

    @staticmethod
    def handle_http_error(exc: HTTPError):
        if exc.response is not None:
            response_payload = exc.response.json()
            if "message" in response_payload:
                print(f":warning: [bold red]{response_payload['message']}[/bold red]")
                return

        print(f":warning: [bold red]HTTP Error: {exc.response.json()}[/bold red]")

    def __call__(self, *args, **kwargs):
        try:
            super(DatazoneTyper, self).__call__(*args, **kwargs)
        except DatazoneError as datazone_exception:
            self.handle_datazone_error(datazone_exception)
        except Exception as e:
            if debug_mode:
                raise e
            else:
                print("[bold red]Unknown error occurred. Please contact support.[/bold red]")
