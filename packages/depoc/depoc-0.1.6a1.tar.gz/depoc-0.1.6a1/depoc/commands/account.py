import depoc
import click
import sys

from rich.console import Console

from .utils._response import _handle_response
from .utils._format import _format_profile


client = depoc.DepocClient()
console = Console()


@click.group
def account() -> None:
    ''' Manage user account '''
    pass

@account.command
@click.option('-n', '--name')
@click.option('-e', '--email')
@click.option('-u', '--username')
def update(name: str, email: str, username: str) -> None:
    if not any([
       name, email, username
    ]):
        console.print('🚨 Specify a field to update')
        sys.exit()
    data = {}
    data.update({'name': name}) if name else None
    data.update({'email': email}) if email else None
    data.update({'username': username}) if username else None

    service = client.accounts.update

    if obj := _handle_response(service, data):
        _format_profile(obj, '[green]UPDATED', update=True)

@account.command
def delete() -> None:
    service = client.accounts.delete

    while True:
        prompt = click.style('Proceed to deletion? [y/n] ', fg='red')
        confirmation = input(prompt)
        if confirmation == 'n':
            sys.exit(0)
        elif confirmation == 'y':
            break

    if obj := _handle_response(service):
        _format_profile(obj, '[red]DEACTIVATED', delete=True)
