import typer
from rich import print
from datazone.cli.datazone_typer import DatazoneTyper

from datazone.cli.execution.main import app as execution_app
from datazone.cli.dataset.main import app as dataset_app
from datazone.cli.source.main import app as source_app
from datazone.cli.extract.main import app as extract_app
from datazone.cli.schedule.main import app as schedule_app
from datazone.cli.project.main import app as project_app
from datazone.cli.pipeline.main import app as pipeline_app
from datazone.cli.auth.main import app as auth_app
from datazone.cli.profile.main import app as profile_app
from datazone.cli.view.main import app as view_app
from datazone.cli.endpoint.main import app as endpoint_app
from datazone.cli.app.main import app as app_app
from datazone.cli.sql.main import sql
from datazone.context import profile_context
from datazone.core.common.settings import SettingsManager

from datazone.cli.run.main import run


app = DatazoneTyper()
app.add_typer(
    execution_app,
    name="execution",
    help="Run pipelines and extracts, view execution logs and history",
)
app.add_typer(
    dataset_app,
    name="dataset",
    help="View, list, and manage datasets and their transactions",
)
app.add_typer(
    source_app, name="source", help="Create, list, and delete data source connections",
)
app.add_typer(
    extract_app,
    name="extract",
    help="Create, execute, and manage data extraction operations",
)
app.add_typer(
    schedule_app,
    name="schedule",
    help="Create and manage scheduled tasks for extracts and pipelines",
)
app.add_typer(
    project_app,
    name="project",
    help="Create, clone, deploy projects and view project activities",
)
app.add_typer(
    pipeline_app,
    name="pipeline",
    help="Create, list, and delete data transformation pipelines",
)
app.add_typer(
    auth_app, name="auth", help="Authenticate and test authentication credentials",
)
app.add_typer(
    profile_app,
    name="profile",
    help="Create, list, and manage CLI profiles and settings",
)
app.add_typer(
    view_app, name="view", help="Create, list, and delete SQL views on datasets",
)
app.add_typer(
    endpoint_app, name="endpoint", help="Create, list, and delete API endpoints",
)
app.add_typer(app_app, name="app", help="List and manage intelligent applications")

app.command()(run)
app.command()(sql)


@app.command()
def version():
    """Show the current version of datazone."""
    import pkg_resources

    my_version = pkg_resources.get_distribution("datazone").version

    print(f"Current version: {my_version}")


@app.command()
def info():
    """Show current user information."""
    profile = SettingsManager.get_profile()
    masked_api_key = profile.api_key[:8] + "****"
    print(f"User: {masked_api_key}")


@app.callback()
def profile_context_callback(
    profile: str = typer.Option(
        default=None, help="Profile to use", envvar="DATAZONE_PROFILE",
    ),
):
    """
    Manage users in the awesome CLI app.
    """
    profile_context.set(profile)
