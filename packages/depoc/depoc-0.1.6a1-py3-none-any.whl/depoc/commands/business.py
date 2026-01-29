import depoc
import click
import sys

from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from .utils._response import _handle_response
from .utils._format import _format_business


client = depoc.DepocClient()
console = Console()


@click.group(invoke_without_command=True)
@click.pass_context
def business(ctx) -> None:
    ''' Maange Business. '''
    if ctx.invoked_subcommand is None:
        service = client.business.get
        if response := _handle_response(service):
            _format_business(response, response.legal_name)

@business.command
def create() -> None:
    ''' Create business. '''
    panel = Panel('[bold]+ CREATE BUSINESS')
    console.print(panel)

    data: dict[str, Any] = {}
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

    service = client.business.create

    if response := _handle_response(service, data):
        _format_business(response, response.legal_name)

@business.command
@click.option('-l', '--legal_name')
@click.option('-t', '--trade_name')
@click.option('-p', '--phone')
@click.option('-e', '--email')
@click.option('--cnpj')
@click.option('--ie')
@click.option('--im')
@click.option('--city')
@click.option('--address')
@click.option('--postcode')
@click.option('--state')
@click.option('-A', '--activate', is_flag=True)
def update(
    legal_name: str,
    trade_name: str,
    cnpj: str,
    ie: str,
    im: str,
    phone: str,
    email: str,
    postcode: str,
    city: str,
    state: str,
    address: str,
    activate: bool,
    ) -> None:
    ''' Update the business. '''
    if not any([
        legal_name, trade_name, cnpj, ie, im, phone,
        email, postcode, city, state, address, activate
    ]):
        console.print('🚨 Specify a field to update')
        sys.exit()

    data: dict[str, Any] = {}
    data.update({'legal_name': legal_name}) if legal_name else None
    data.update({'trade_name': trade_name}) if trade_name else None
    data.update({'cnpj': cnpj}) if cnpj else None
    data.update({'ie': ie}) if ie else None
    data.update({'im': im}) if im else None
    data.update({'phone': phone}) if phone else None
    data.update({'email': email}) if email else None
    data.update({'postcode': postcode}) if postcode else None
    data.update({'city': city}) if city else None
    data.update({'state': state}) if state else None
    data.update({'address': address}) if address else None
    data.update({'is_active': True}) if activate else None

    service = client.business.update

    if response := _handle_response(service, data):
        _format_business(response, 'UPDATED', update=True)

@business.command
def delete() -> None:
    ''' Delete the business. '''
    service = client.business.delete

    while True:
        prompt = click.style('Proceed to deletion? [y/n] ', fg='red')
        confirmation = input(prompt)
        if confirmation == 'n':
            sys.exit(0)
        elif confirmation == 'y':
            break

    if _handle_response(service):
        console.print('✅ Business inactivated')
