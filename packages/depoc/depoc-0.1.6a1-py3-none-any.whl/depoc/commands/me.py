import depoc
import click

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .utils._response import _handle_response
from .utils._format import _format_profile


client = depoc.DepocClient()


@click.command
def me() -> None:
    ''' Get the current user's data'''
    service = client.me.get

    if obj := _handle_response(service):
        _format_profile(obj, 'USER PROFILE')
