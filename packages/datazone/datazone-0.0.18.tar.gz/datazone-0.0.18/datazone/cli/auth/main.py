from rich import print
import typer

from datazone.core.connections.auth import AuthService


def test():
    user_data = AuthService.check_session()
    print(f"Hello {user_data.get('full_name', '')}, you are logged in!")


app = typer.Typer()
app.command()(test)
