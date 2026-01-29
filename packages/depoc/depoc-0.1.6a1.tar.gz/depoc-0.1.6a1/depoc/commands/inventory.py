import depoc
import click
import sys

from typing import Any

from .utils._response import _handle_response
from .utils._format import (
    page_summary, 
    _format_inventory,
    _format_transaction_inventory
)

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt


client = depoc.DepocClient()
console = Console()


@click.group(invoke_without_command=True)
@click.option('-l', '--limit', default=50)
@click.option('-p', '--page', default=0)
@click.pass_context
def inventory(ctx, limit: int, page: int) -> None:
    ''' Manage product inventory. '''
    if ctx.invoked_subcommand is None:
        service = client.inventory.all
        
        if response := _handle_response(
            service,
            limit=limit,
            page=page
        ):
            page_summary(response)

            for obj in response.results:
               _format_inventory(obj)


@inventory.command
@click.argument('inventory_id')
def get(inventory_id: str) -> None:
    ''' Retrieve a product specific inventory. '''
    service = client.product_inventory.get

    if obj := _handle_response(service, resource_id=inventory_id):
        _format_inventory(obj)


@inventory.command
@click.argument('inventory_id')
@click.option('-l', '--location', required=True)
def udpate(inventory_id: str, location: str) -> None:
    ''' Update location of product specific inventory. '''
    data: dict[str, Any] = {'location': location}
    service = client.product_inventory.update

    if obj := _handle_response(service, data, resource_id=inventory_id):
        _format_inventory(obj, update=True)


@inventory.group(invoke_without_command=True)
@click.option('-id', '--inventory-id', required=True)
@click.option('-l', '--limit', default=50)
@click.option('-p', '--page', default=0)
@click.pass_context
def t(ctx, inventory_id: str, limit: int, page: int) -> None:
    ''' Retrieve all transactions of a product inventory. '''
    if ctx.invoked_subcommand is None:
        service = client.inventory_transaction.all

        if response := _handle_response(
            service,
            limit=limit,
            page=page,
            resource_id=inventory_id,
        ):
            page_summary(response)
            for obj in response.results:
                _format_transaction_inventory(obj)


@t.command
@click.argument('transaction_id')
def get(transaction_id) -> None:
    ''' Retrieve an specific transaction of a product inventory. '''
    service = client.inventory_transaction_id.get

    if obj := _handle_response(service, resource_id=transaction_id):
        _format_transaction_inventory(obj)


@t.command
@click.argument('inventory_id')
def create(inventory_id: str) -> None:
    ''' Create a new inventory transaction. '''
    panel = Panel('[bold]+ ADD NEW INVENTORY TRANSACTION')
    console.print(panel)

    data: dict[str, Any] = {}
    data.update({'type': Prompt.ask('Type', choices=['inbound', 'outbound'])})
    console.rule('',style=None, align='left')
    data.update({'date': Prompt.ask('Date', default=None)})
    console.rule('',style=None, align='left')
    data.update({'quantity': Prompt.ask('Quantity', default=None)})
    console.rule('',style=None, align='left')
    data.update({'unit_cost': Prompt.ask('Unit Cost', default=None)})
    console.rule('',style=None, align='left')
    data.update({'unit_price': Prompt.ask('Unit Price', default=None)})
    console.rule('',style=None, align='left')
    data.update({'description': Prompt.ask('Description', default=None)})
    console.rule('',style=None, align='left')

    service = client.inventory_transaction.create
    if response := _handle_response(service, data, resource_id=inventory_id):
        _format_transaction_inventory(response)


@t.command
@click.argument('transaction')
@click.option('-q' ,'--quantity')
@click.option('-c' ,'--unit-cost')
@click.option('-p' ,'--unit-price')
@click.option('-d' ,'--description')
def update(
    transaction,
    quantity,
    unit_cost,
    unit_price,
    description
) -> None:
    ''' Update an specific inventory transaction. '''
    if not any([quantity, unit_cost, unit_price, description]):
        console.print('🚨 Specify a field to update')
        sys.exit()

    data: dict[str, Any] = {}
    data.update({'quantity': quantity}) if quantity else None
    data.update({'unit_cost': unit_cost}) if unit_cost else None
    data.update({'unit_price': unit_price}) if unit_price else None
    data.update({'description': description}) if description else None

    service = client.inventory_transaction_id.update
    if response := _handle_response(
        service,
        data,
        resource_id=transaction,
    ):
        _format_transaction_inventory(response, update=True)


@t.command
@click.argument('id')
def delete(id: str) -> None:
    ''' Delete an specific inventory transaction. '''
    service = client.inventory_transaction_id.delete

    while True:
        prompt = click.style('Proceed to deletion? [y/n] ', fg='red')
        confirmation = input(prompt)
        if confirmation == 'n':
            sys.exit(0)
        elif confirmation == 'y':
            break

    if _handle_response(service, resource_id=id):
        console.print('✅ Inventory transaction deleted')
