import depoc
import click
import sys

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .utils._response import _handle_response


client = depoc.DepocClient()


@click.command
@click.option('-d', '--date')
@click.option('-s', '--start-date')
@click.option('-e', '--end-date')
def balance(date: str, start_date: str, end_date: str) -> None:
    ''' Balance for a specific period. '''
    if not any([date, start_date, end_date]):
        date = 'week'
        params = {'date': date}
    elif date and not any([start_date, end_date]):
        params = {'date': date}
    elif start_date and end_date:
        params = {'start_date': start_date, 'end_date': end_date}
    else:
        console.print(
            '📅 [bold][-s] [--start-date] \n[/bold]'
            '📅 [bold][-e] [--end-date] \n[/bold]'
            '🚨 Must be specified as a pair'
        )
        sys.exit()
    
    caption = date
    if start_date and end_date:
        caption = f'{start_date} → {end_date}'
    elif date in ('week', 'month'):
        caption = f"this {date}'s balance"
    elif date == 'today':
        caption = f"today's balance"

    income: float = 0
    expenses: float = 0
    balance: float = 0
    
    service = client.financial_transactions.filter

    if response := _handle_response(
        service,
        **params,
        ):

        for obj in response.results:
            if obj.type == 'credit':
                income += float(obj.amount)
            elif obj.type == 'debit':
                expenses += float(obj.amount)

        has_next_page: bool = response.next is not None
        next_page = 2
        while has_next_page:
            response_ = _handle_response(service, **params, page=next_page)

            for obj in response_.results:
                if obj.type == 'credit':
                    income += float(obj.amount)
                elif obj.type == 'debit':
                    expenses += float(obj.amount)

            next_page += 1
            has_next_page = False if not response_.next else True

        balance = round(income + expenses, 2)

        table = Table(
            show_header=True,
            show_footer=True,
            box=None,
            expand=True,
            caption=caption,
            title=f'[bold]R${balance:,.2f}'
            )
        
        table.add_column('', justify='left', no_wrap=True)
        table.add_column('', justify='right', no_wrap=True)
        table.add_row('📈 Income', f'R${income:,.2f}')
        table.add_row('📉 Expenses', f'R${abs(expenses):,.2f}')

        border_style = 'red' if balance < 0 else 'green'

        profile = Panel(
            table,
            title=f'[bold]BALANCE',
            title_align='left',
            border_style=border_style,
        )

        console = Console()
        console.print(profile)
