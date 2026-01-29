import typer
from rich import print
from rich.console import Console
from rich.table import Table

from datazone.service_callers.datazone import DatazoneServiceCaller


def sql(
    query: str = typer.Argument(..., help="SQL query to run"),
    project_id: str = typer.Option(..., help="Project ID to execute SQL against"),
    size: int = typer.Option(10, help="Max rows to show"),
):
    """Execute a SQL query and print the results. Prefer --project-id."""
    rows = DatazoneServiceCaller.execute_sql(query=query, project_id=project_id)
    if not rows:
        print("[bold orange]No data[/bold orange]")
        return

    rows = rows[:size]
    table = Table(*rows[0].keys())
    for r in rows:
        table.add_row(*[str(v) for v in r.values()])
    Console().print(table)
