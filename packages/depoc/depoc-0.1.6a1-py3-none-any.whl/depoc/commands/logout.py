import depoc
import json
import click

from rich.console import Console


console = Console()
        

@click.command(help='Logout of your account')
def logout() -> None:
    with open(depoc.token_path, 'w') as f:
        console.clear()
        console.print('🫂  bye bye, see you soon.')
        json.dump({'token': None}, f)
