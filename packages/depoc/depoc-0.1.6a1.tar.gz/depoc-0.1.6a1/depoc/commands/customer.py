import depoc
import click
import time
import sys

from typing import Any

from .utils._response import _handle_response
from .utils._format import spinner, page_summary, _format_contact

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt


client = depoc.DepocClient()
console = Console()


@click.group(invoke_without_command=True)
@click.pass_context
@click.option('-l', '--limit', default=50)
@click.option('-p', '--page', default=0)
def customer(ctx, limit: int, page: int) -> None:
    ''' Manage customers. '''
    if ctx.invoked_subcommand is None:
        service = client.customers.all
        
        if response := _handle_response(service, limit=limit, page=page):
            page_summary(response)

            for obj in response.results:
                _format_contact(obj, f'{obj.name}')


@customer.command
def create() -> None:
    ''' Create customer. '''
    panel = Panel('[bold]+ ADD NEW CUSTOMER')
    console.print(panel)

    data: dict[str, Any] = {}
    data.update({'code': Prompt.ask('🆔 Code', default=None)})
    console.rule('',style=None, align='left')
    data.update({'name': Prompt.ask('✏️  Name', default=None)})
    console.rule('',style=None, align='left')
    data.update({'alias': Prompt.ask('✏️  Alias', default=None)})
    console.rule('',style=None, align='left')
    data.update({'gender': Prompt.ask('⚧️  Gender', choices=['male', 'female'])})
    console.rule('',style=None, align='left')
    data.update({'cpf': Prompt.ask('📋 CPF', default=None)})
    console.rule('',style=None, align='left')
    data.update({'phone': Prompt.ask('📱 Phone', default=None)})
    console.rule('',style=None, align='left')
    data.update({'email': Prompt.ask('✉️  Email', default=None)})
    console.rule('',style=None, align='left')
    data.update({'postcode': Prompt.ask('📮 Postal Code', default=None)})
    console.rule('',style=None, align='left')
    data.update({'city': Prompt.ask('🏙️  City', default=None)})
    console.rule('',style=None, align='left')
    data.update({'state': Prompt.ask('🗺️  State', default=None)})
    console.rule('',style=None, align='left')
    data.update({'address': Prompt.ask('📍 Address', default=None)})
    console.rule('',style=None, align='left')
    data.update({'notes': Prompt.ask('🗒️  Notes', default=None)})
    console.rule('',style=None, align='left')

    service = client.customers.create

    if obj := _handle_response(service, data):
        _format_contact(obj, obj.name)

@customer.command
@click.argument('id')
def get(id: str) -> None:
    ''' Retrieve an specific customer. '''
    service = client.customers.get

    if obj := _handle_response(service, resource_id=id):
        _format_contact(obj, obj.name)

@customer.command
@click.argument('id')
@click.option('-c', '--code')
@click.option('-n', '--name')
@click.option('-a', '--alias')
@click.option('-g', '--gender')
@click.option('-p', '--phone')
@click.option('-e', '--email')
@click.option('-s', '--state')
@click.option('--cpf')
@click.option('--city')
@click.option('--notes')
@click.option('--address')
@click.option('--postcode')
@click.option('-A', '--activate', is_flag=True)
def update(
    id: str,
    code: str,
    name: str,
    alias: str,
    gender: str,
    cpf: str,
    notes: str,
    phone: str,
    email: str,
    postcode: str,
    city: str,
    state: str,
    address: str,
    activate: bool,
    ) -> None:
    ''' Update an specific customer. '''
    if not any([
       code, name, alias, gender, cpf, notes, phone, email,
       postcode, city, state, address, activate
    ]):
        console.print('🚨 Specify a field to update')
        sys.exit()

    data: dict[str, Any] = {}
    data.update({'code': code}) if code else None
    data.update({'name': name}) if name else None
    data.update({'alias': alias}) if alias else None
    data.update({'gender': gender}) if gender else None
    data.update({'cpf': cpf}) if cpf else None
    data.update({'notes': notes}) if notes else None
    data.update({'phone': phone}) if phone else None
    data.update({'email': email}) if email else None
    data.update({'postcode': postcode}) if postcode else None
    data.update({'city': city}) if city else None
    data.update({'state': state}) if state else None
    data.update({'address': address}) if address else None
    data.update({'is_active': True}) if activate else None

    service = client.customers.update

    if obj := _handle_response(service, data, resource_id=id):
        _format_contact(obj, 'UPDATED', update=True)

@customer.command
@click.argument('ids', nargs=-1)
def delete(ids: str) -> None:
    ''' Delete an specific customer. '''
    service = client.customers.delete

    while True:
        prompt = click.style('Proceed to deletion? [y/n] ', fg='red')
        confirmation = input(prompt)
        if confirmation == 'n':
            sys.exit(0)
        elif confirmation == 'y':
            break

    if len(ids) > 1:
        spinner()

    for id in ids:
        time.sleep(0.5)
        if _handle_response(service, resource_id=id):
            console.print('✅ Customer inactivated')
