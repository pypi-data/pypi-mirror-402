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
def supplier(cxt, limit: int, page: int) -> None:
    ''' Manage suppliers. '''
    if cxt.invoked_subcommand is None:
        service = client.suppliers.all
        
        if response := _handle_response(service, limit=limit, page=page):
            page_summary(response)

            for obj in response.results:
                _format_contact(obj, f'{obj.legal_name}')


@supplier.command
def create() -> None:
    ''' Create supplier. '''
    panel = Panel('[bold]+ ADD NEW SUPPLIER')
    console.print(panel)

    data: dict[str, Any] = {}
    data.update({'code': Prompt.ask('🆔 Code', default=None)})
    console.rule('',style=None, align='left')
    data.update({'legal_name': Prompt.ask('✏️  Legal Name', default=None)})
    console.rule('',style=None, align='left')
    data.update({'trade_name': Prompt.ask('™️  Trade Name', default=None)})
    console.rule('',style=None, align='left')
    data.update({'cnpj': Prompt.ask('📋 CNPJ', default=None)})
    console.rule('',style=None, align='left')
    data.update({'ie': Prompt.ask('📋 IE', default=None)})
    console.rule('',style=None, align='left')
    data.update({'im': Prompt.ask('📋 IM', default=None)})
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

    service = client.suppliers.create

    if obj := _handle_response(service, data):
        _format_contact(obj, obj.legal_name)

@supplier.command
@click.argument('id')
def get(id: str) -> None:
    ''' Retrieve an specific supplier. '''
    service = client.suppliers.get

    if obj := _handle_response(service, resource_id=id):
        _format_contact(obj, obj.legal_name)

@supplier.command
@click.argument('id')
@click.option('-c', '--code')
@click.option('-l', '--legal_name')
@click.option('-t', '--trade_name')
@click.option('-p', '--phone')
@click.option('-e', '--email')
@click.option('-s', '--state')
@click.option('--cnpj')
@click.option('--ie')
@click.option('--im')
@click.option('--notes')
@click.option('--city')
@click.option('--address')
@click.option('--postcode')
@click.option('-A', '--activate', is_flag=True)
def update(
    id: str,
    code: str,
    legal_name: str,
    trade_name: str,
    cnpj: str,
    ie: str,
    im: str,
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
       code, legal_name, trade_name, ie, im, cnpj, notes,
       phone, email, postcode, city, state, address, activate,
    ]):
        console.print('🚨 Specify a field to update')
        sys.exit()
    data: dict[str, Any] = {}
    data.update({'code': code}) if code else None
    data.update({'legal_name': legal_name}) if legal_name else None
    data.update({'trade_name': trade_name}) if trade_name else None
    data.update({'cnpj': cnpj}) if cnpj else None
    data.update({'ie': ie}) if ie else None
    data.update({'im': im}) if im else None
    data.update({'notes': notes}) if notes else None
    data.update({'phone': phone}) if phone else None
    data.update({'email': email}) if email else None
    data.update({'postcode': postcode}) if postcode else None
    data.update({'city': city}) if city else None
    data.update({'state': state}) if state else None
    data.update({'address': address}) if address else None
    data.update({'is_active': True}) if activate else None

    service = client.suppliers.update

    if obj := _handle_response(service, data, resource_id=id):
        _format_contact(obj, 'UPDATED', update=True)

@supplier.command
@click.argument('ids', nargs=-1)
def delete(ids: str) -> None:
    ''' Delete an specific supplier. '''
    service = client.suppliers.delete

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
            console.print('✅ Supplier inactivated')
