import depoc
import click
import sys
import time

from typing import Any

from rich.console import Console
from rich.console import group
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt

from .utils._response import _handle_response
from .utils._format import (
    spinner, 
    page_summary,
    _format_category,
    _format_transactions
)


client = depoc.DepocClient()
console = Console()


@group()
def get_tables(tables: list):
    for table in tables:
        yield table

@click.group
def f() -> None:
    ''' Manage financial categories and transactions'''

@f.group(invoke_without_command=True)
@click.pass_context
@click.option('-l', '--limit', default=50)
@click.option('-p', '--page', default=0)
def category(ctx, limit: int, page: int) -> None:
    ''' Manage financial categories '''
    if ctx.invoked_subcommand is None:
        service = client.financial_categories.all

        if response := _handle_response(service, limit=limit, page=page):
            # I want to include the is_active
            # attr into the categories dict
            categories: dict[str, dict] = {}
            for obj in response.results:
                if not obj.parent:
                    categories.update({obj.name: {'id': obj.id}})

            for obj in response.results:
                if obj.parent:
                    parent = obj.parent
                    while parent:
                        if parent.name not in categories.keys():
                            child = categories[parent.parent.name][parent.name]
                            if child:
                                child.update({
                                    'id': parent.id,
                                    obj.name: {'id': obj.id}
                                })
                        elif obj.parent.name in categories.keys():
                            categories[parent.name].update({
                                obj.name: {'id': obj.id}
                            })
                        parent = parent.parent

            for k, v in categories.items():
                table = Table(
                    show_header=True,
                    show_footer=True,
                    box=None,
                    expand=True,
                    )
                
                table.add_column('', justify='left', no_wrap=True)
                table.add_column('', justify='right', no_wrap=True)

                tables = [table]

                for name, value in v.items():
                    if isinstance(value, dict):
                        if len(value) > 1:
                            sub = Table(
                                show_header=True,
                                show_footer=True,
                                box=None,
                                expand=True,
                            )

                            sub.add_column(name, justify='left', no_wrap=True)
                            sub.add_column(value['id'], justify='right', no_wrap=True)

                            for a, b in value.items():
                                if a != 'id':
                                    sub.add_row(
                                        f'[bright_black]{a}',
                                        f'[bright_black]{b['id']}'
                                    )
                            tables.append(sub)
                        else:
                            table.add_row(name, value['id'])

                group = get_tables(tables)

                profile = Panel(
                    group,
                    title=f'[bold]{k.upper()}',
                    title_align='left',
                    subtitle=v['id'],
                    subtitle_align='left',
                )

                console.print(profile)

@category.command
@click.argument('name')
@click.option('-p', '--parent', help='Inform the Parent Caregory if any.')
def create(name: str, parent: str) -> None:
    ''' Create a new category. '''
    data: dict[str, Any] = {'name': name}
    data.update({'parent': parent}) if parent else None

    service = client.financial_categories.create
    if obj := _handle_response(service, data):
        _format_category(obj, highlight=True)


@category.command
@click.argument('id')
def get(id: str) -> None:
    ''' Retrieve an specific category '''
    service = client.financial_categories.get
    if obj := _handle_response(service, resource_id=id):
        _format_category(obj)

@category.command
@click.argument('id')
@click.option('--name', help='Inform the new name for the Category.')
@click.option('--parent', help='Inform the Parent Caregory if any.')
@click.option('--activate', is_flag=True, help='Activate category.')
def update(id: str, name: str, parent: str, activate: bool) -> None:
    ''' Update a category '''
    data: dict[str, Any] = {}
    data.update({'name': name}) if name else None
    data.update({'parent': parent}) if parent else None
    data.update({'is_active': True}) if activate else None

    service = client.financial_categories.update

    if obj := _handle_response(service, data, id):
        _format_category(obj, highlight=True)

@category.command
@click.argument('ids', nargs=-1)
def delete(ids: str) -> None:
    ''' Delete a category '''
    service = client.financial_categories.delete

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
            console.print('✅ Category inactivated')


@f.group(invoke_without_command=True)
@click.pass_context
@click.option('-l', '--limit', default=50)
@click.option('-p', '--page', default=0)
@click.option('-b', '--bank')
def transaction(ctx, limit: int, page: int, bank: str) -> None:
    ''' Manage financial transactions '''
    if ctx.invoked_subcommand is None:
        service = client.financial_transactions.all

        if response := _handle_response(service, limit=limit, page=page):
            results = response.results

            if bank:
                results = [
                    obj for obj in results if obj.account.name == bank.title()
                ]
                # This page summary data needs to be
                # reviewed to accommodate different cases
                results_count = len(results)
                click.echo((
                    f'\n[Page {1}/{1}] '
                    f'Showing {results_count} results '
                    f'(Total: {results_count})\n'
                ))
            else:
                page_summary(response)

        income = 0
        expenses = 0
        for obj in results:
            if obj.type == 'credit':
                income += float(obj.amount)
            elif obj.type == 'debit':
                expenses += float(obj.amount)
            title = f'\n{obj.account.name} {obj.type}'.upper()
            _format_transactions(obj, title)

        balance = income - abs(expenses)

        format_income = f'[yellow]R${income:,.2f}[/yellow]'
        format_expenses = f'[yellow]R${abs(expenses):,.2f}[/yellow]'
        format_balance = f'[yellow]R${balance:,.2f}[/yellow]'

        message = (
            f'\n{'[bold]📈 Income: ' + format_income}\n'
            f'\n{'[bold]📉 Expenses: ' + format_expenses}\n'
            f'\n{'[bold]💵 Balance: ' + format_balance}\n'
        )
        console.print(message)

@transaction.command
@click.option('-c', '--credit', is_flag=True)
@click.option('-d', '--debit', is_flag=True)
@click.option('-t', '--transfer', is_flag=True)
def create(
    credit: bool,
    debit: bool,
    transfer: bool,
) -> None:
    if not any([credit, debit, transfer]):
        message = (
            '🚨 Inform a type of transaction: '
            '-c (credit), -d (debit) or -t (transfer).'
        )
        console.print((
            '🚨 Inform a type of transaction:'
            '\n🏧 [bold][-t][/bold] [bold][--transfer][/bold]'
            '\n🏧 [bold][-c][/bold] [bold][--credit][/bold]'
            '\n🏧 [bold][-d][/bold] [bold][--debit][/bold]'
        ))
        sys.exit(0)

    panel = Panel('[bold]+ ADD NEW TRANSACTION')
    console.print(panel)

    data: dict[str, Any] = {}
    data.update({'amount': Prompt.ask('💰 Amount R$', default=None)})
    console.rule('',style=None, align='left')
    data.update({'account': Prompt.ask('🏦 Account', default=None)})
    console.rule('',style=None, align='left')
    data.update({'send_to': Prompt.ask('🏦 Send to')}) if transfer else None
    console.rule('',style=None, align='left') if transfer else None
    data.update({'description': Prompt.ask('🗒️  Description', default=None)})
    console.rule('',style=None, align='left')
    data.update({'category': Prompt.ask('📂 Category', default=None)})
    console.rule('',style=None, align='left')
    data.update({'contact': Prompt.ask('👤 Contact', default=None)})
    console.rule('',style=None, align='left')

    if credit:
        data.update({'type': 'credit'})
    elif debit:
        data.update({'type': 'debit'})
    elif transfer:
        data.update({'type': 'transfer'})

    service = client.financial_transactions.create

    if obj := _handle_response(service, data):
        title = f'\n{obj.account.name} {obj.type}'.upper()
        _format_transactions(obj, title)

@transaction.command
@click.argument('id')
def get(id: str) -> None:
    ''' Retrieve an specific transaction. '''
    service = client.financial_transactions.get
    if obj := _handle_response(service, resource_id=id):
        title = f'\n{obj.account.name} {obj.type}'.upper()
        _format_transactions(obj, title)

@transaction.command
@click.argument('ids', nargs=-1)
def delete(ids: str) -> None:
    ''' Delete an specific transaction. '''
    service = client.financial_transactions.delete

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
            console.print('✅ Transaction deleted')

@transaction.command
@click.argument('search', required=False)
@click.option('-d', '--date')
@click.option('-s', '--start-date')
@click.option('-e', '--end-date')
@click.option('-b', '--bank')
@click.option('-l', '--limit', default=50)
@click.option('-p', '--page', default=0)
@click.pass_context
def search(
    ctx,
    search: str,
    date: str,
    start_date: str,
    end_date: str,
    bank: str,
    limit: int,
    page: int,
    ) -> None:
    ''' Filter transactions. '''
    if not any([search, date, start_date, end_date]):
        click.echo(ctx.get_help())
        sys.exit(0)

    service = client.financial_transactions.filter

    if response := _handle_response(
        service,
        search=search,
        date=date,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        page=page,
    ):
        results = response.results
        if bank:
            results = [
                obj for obj in results if obj.account.name == bank.title()
            ]
            # This page summary data needs to be
            # reviewed to accommodate different cases
            results_count = len(results)
            click.echo((
                f'\n[Page {1}/{1}] '
                f'Showing {results_count} results '
                f'(Total: {results_count})\n'
            ))
        else:
            page_summary(response)

        income = 0
        expenses = 0
        for obj in results:
            if obj.type == 'credit':
                income += float(obj.amount)
            elif obj.type == 'debit':
                expenses += float(obj.amount)
            title = f'\n{obj.account.name} {obj.type}'.upper()
            _format_transactions(obj, title)

        balance = income - abs(expenses)

        format_income = f'[yellow]R${income:,.2f}[/yellow]'
        format_expenses = f'[yellow]R${abs(expenses):,.2f}[/yellow]'
        format_balance = f'[yellow]R${balance:,.2f}[/yellow]'

        message = (
            f'\n{'[bold]📈 Income: ' + format_income}\n'
            f'\n{'[bold]📉 Expenses: ' + format_expenses}\n'
            f'\n{'[bold]💵 Balance: ' + format_balance}\n'
        )
        console.print(message)
