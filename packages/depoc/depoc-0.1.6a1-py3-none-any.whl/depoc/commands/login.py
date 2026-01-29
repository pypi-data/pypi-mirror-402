import json
import depoc
import click

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.align import Align

from depoc.utils._error import APIError

console = Console()


@click.command()
@click.option('--username', prompt=True, required=True)
@click.password_option(required=True, confirmation_prompt=False)
def login(username: str, password: str) -> None :
    ''' Enter in your account '''
    auth = depoc.Connection(username, password)
    
    try:
        depoc.token = auth.token
        console.clear()
        title = Text(
            "🔐 LOGIN SUCCESSFUL",
            justify="center",
            style="bold green"
        )
        console.print(Align.center(Panel(title, expand=False)))

        with open(depoc.token_path, 'w') as f:
            json.dump({'token': auth.token}, f)
            
    except APIError as e:
        console.clear()
        title = Text(
            f"🚨 LOGIN FAILED",
            justify="center",
            style="bold red"
        )
        console.print(Align.center(Panel(title, expand=False)))
        console.print(Align.center(str(e.message)))
