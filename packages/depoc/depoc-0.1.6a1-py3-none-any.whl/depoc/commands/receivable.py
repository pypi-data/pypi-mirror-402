import depoc
import click
import sys
import time

from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from .utils._response import _handle_response
from .utils._format import (
    spinner,
    page_summary,
    _format_payments,
    _format_transactions,
)


client = depoc.DepocClient()
console = Console()


@click.group(invoke_without_command=True)
@click.option('-l', '--limit', default=50)
@click.option('-p', '--page', default=0)
@click.option('--all', is_flag=True)
@click.option('--detail', is_flag=True)
@click.pass_context
def receivable(
    ctx,
    limit: int,
    page: int,
    all: bool = False,
    detail: bool = False
) -> None:
    ''' Manage receivables. '''
    if ctx.invoked_subcommand is None:
        service = client.receivables.all

        if not all and limit != 50: 
            console.print((
                '🚨 [bold][-l][/bold] & [bold][--limit][/bold] requires '
                'the [yellow]--all[/yellow] flag.'
            ))
            sys.exit()

        if not all and page > 0: 
            console.print((
                '🚨 [bold][-p][/bold] & [bold][--page][/bold] requires '
                'the [yellow]--all[/yellow] flag.'
            ))
            sys.exit()

        if response := _handle_response(service, limit=limit, page=page):
            results = sorted(response.results, key=lambda obj: obj.due_at)

            if not all:
                results = [obj for obj in results if obj.status != 'paid']
                results_count = len(results)

                # This page summary data needs to be
                # reviewed to accommodate different cases
                click.echo((
                    f'\n[Page {1}/{1}] '
                    f'Showing {results_count} results '
                    f'(Total: {results_count})\n'
                ))
                console.rule(
                    '[bold]OUTSTANDING RECEIVABLES',
                    align='center',
                    style='bold',
                )
            else:
                page_summary(response)
                console.rule('ALL RECEIVABLES', align='center', style='none')
            
            console.print('')

            total_receivable: float = 0
            for obj in results:
                total_receivable += float(obj.outstanding_balance)             
                _format_payments(obj, obj.contact, detail=detail)

            format_total = f'[yellow]R${total_receivable:,.2f}'
            message = f'\n{'[bold]💵 Total to be received: ' + format_total}\n'
            console.print(message)

@receivable.command
def create() -> None:
    ''' Create receivable. '''
    panel = Panel('[bold]+ ADD NEW RECEIVABLE')
    console.print(panel)

    data: dict[str, Any] = {}
    data.update({'total_amount': Prompt.ask('💰 Total Amount R$', default=None)})
    console.rule('',style=None, align='left')
    data.update({'due_at': Prompt.ask('📅 Due At', default=None)})
    console.rule('',style=None, align='left')
    data.update({'issued_at': Prompt.ask('📅 Issued At', default=None)})
    console.rule('',style=None, align='left')
    data.update({'payment_method': Prompt.ask('💳 Payment Method', default=None)})
    console.rule('',style=None, align='left')
    recurrence = Prompt.ask('⏳ Recurrence', default=None, choices=['once', 'weekly', 'monthly', 'installments'])
    data.update({'recurrence': recurrence})
    console.rule('',style=None, align='left')

    if recurrence == 'monthly':
        console.rule('',style=None, align='left')
        data.update({'due_day_of_month': Prompt.ask('📆 Due Day of Month', default=None)})
    elif recurrence == 'weekly':
        console.rule('',style=None, align='left')
        data.update({'due_weekday': Prompt.ask('📆 Due Weekday', default=None)})
    elif recurrence == 'installments':
        console.rule('',style=None, align='left')
        data.update({'installment_count': Prompt.ask('⏰ Installments', default=None)})
        console.rule('',style=None, align='left')
        data.update({'due_day_of_month': Prompt.ask('📆 Due Day of Month', default=None)})


    data.update({'category': Prompt.ask('📂 Category ID', default=None)})
    console.rule('',style=None, align='left')
    data.update({'contact': Prompt.ask('🆔 Contact ID', default=None)})
    console.rule('',style=None, align='left')
    data.update({'reference': Prompt.ask('📎 Reference Number', default=None)})
    console.rule('',style=None, align='left')
    data.update({'notes': Prompt.ask('🗒️  Notes', default=None)})
    console.rule('',style=None, align='left')

    service = client.receivables.create

    if obj := _handle_response(service, data):
        _format_payments(obj, obj.contact, detail=True)

@receivable.command
@click.argument('id')
def get(id: str) -> None:
    ''' Retrieve an specific receivable. '''
    service = client.receivables.get
    if obj := _handle_response(service, resource_id=id):
        _format_payments(obj, obj.contact, detail=True)

@receivable.command
@click.argument('id')
@click.option('-c', '--contact')
@click.option('-i', '--issued-at')
@click.option('-d', '--due-at')
@click.option('-t', '--total-amount')
@click.option('-p', '--payment-method')
@click.option('-r', '--reference')
@click.option('-n', '--notes')
@click.option('--category')
def update(
    id: str,
    contact: str,
    category: str,
    issued_at: str,
    due_at: str,
    total_amount: float,
    payment_method: str,
    reference: str,
    notes: str,
    ) -> None:
    ''' Update an specific payable. '''
    if not any([
       contact, category, issued_at, due_at, total_amount,
       payment_method, reference, notes,
    ]):
        console.print('🚨 Specify a field to update')
        sys.exit()
    data: dict[str, Any] = {}
    data.update({'contact': contact}) if contact else None
    data.update({'category': category}) if category else None
    data.update({'issued_at': issued_at}) if issued_at else None
    data.update({'due_at': due_at}) if due_at else None
    data.update({'total_amount': total_amount}) if total_amount else None
    data.update({'payment_method': payment_method}) if payment_method else None
    data.update({'reference': reference}) if reference else None
    data.update({'notes': notes}) if notes else None

    service = client.receivables.update
    if obj := _handle_response(service, data, resource_id=id):
        _format_payments(obj, 'UPDATED', update=True, detail=True)

@receivable.command
@click.argument('ids', nargs=-1)
def delete(ids: str) -> None:
    ''' Delete an specific receivable. '''
    service = client.receivables.delete

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
        if obj := _handle_response(service, resource_id=id):
            console.print('✅ Receivable deleted')

@receivable.command
@click.argument('id')
@click.option('--amount', required=True)
@click.option('--account', required=True)
def settle(id: str, amount: float, account: str) -> None:
    ''' Settle a receivable '''
    data: dict[str, Any] = {'amount': amount, 'account': account}

    service = client.receivable_settle.create

    if obj := _handle_response(service, data, id):
        title = f'\n{obj.account.name} {obj.type}'.upper()
        _format_transactions(obj, title)

@receivable.command
@click.argument('search', required=False)
@click.option('-d', '--date')
@click.option('-s', '--start-date')
@click.option('-e', '--end-date')
@click.option('-l', '--limit', default=50)
@click.pass_context
def search(
    ctx,
    search: str,
    date: str,
    start_date: str,
    end_date: str,
    limit: int,
    ) -> None:
    ''' Filter receivables. '''
    if not any([search, date, start_date, end_date]):
        click.echo(ctx.get_help())
        sys.exit(0)

    service = client.receivables.filter

    if response := _handle_response(
        service,
        search=search,
        date=date,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
    ):
        results = sorted(response.results, key=lambda obj: obj.due_at)

        page_summary(response)

        total_receivable: float = 0
        for obj in results:
            total_receivable += float(obj.outstanding_balance)
            _format_payments(obj, obj.contact)

        click.echo(click.style(f'\n{'':-<49}', bold=True))
        format_total = f'[yellow]R${total_receivable:,.2f}'
        message = f'\n{'[bold]💵 Total to be received: ' + format_total}\n'
        console.print(message)
