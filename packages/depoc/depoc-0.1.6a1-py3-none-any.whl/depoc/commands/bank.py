import depoc
import click

from rich.console import Console

from .utils._response import _handle_response
from .utils._format import _format_bank


client = depoc.DepocClient()
console = Console()


@click.group(invoke_without_command=True)
@click.pass_context
def bank(ctx) -> None:
    ''' Manage bank accounts '''
    if ctx.invoked_subcommand is None:
        service = client.financial_accounts.all
        total_balance: float = 0
        if response := _handle_response(service):
            for obj in response.results:
                total_balance += float(obj.balance)
                _format_bank(obj)

            format_total_balance = f'R${total_balance:,.2f}'
            message = f'\n{'💵 Total Balance: ' + format_total_balance}\n'
            click.echo(message)

@bank.command
@click.argument('name')
def create(name: str) -> None:
    ''' Create a new bank account. '''
    data = {'name': name}
    service = client.financial_accounts.create

    if obj := _handle_response(service, data):
        _format_bank(obj)

@bank.command
@click.argument('id')
def get(id: str) -> None:
    ''' Retrieve an specific bank account. '''
    service = client.financial_accounts.get

    if obj := _handle_response(service, resource_id=id):
        _format_bank(obj)

@bank.command
@click.argument('id')
@click.argument('name', required=False)
@click.option('-A', '--activate', is_flag=True)
def update(id: str, name: str, activate: bool = False) -> None:
    ''' Update a bank account. '''
    if name:
        data = {'name': name}
    elif activate:
        data = {'is_active': True}
    elif name and activate:
        data = data = {'name': name, 'is_active': True}

    service = client.financial_accounts.update

    if obj := _handle_response(service, data, id):
        _format_bank(obj, update=True)

@bank.command
@click.argument('id')
def delete(id: str) -> None:
    ''' Delete a bank account. '''
    service = client.financial_accounts.delete

    if _handle_response(service, resource_id=id):
        console.print('✅ Bank account inactivated')
