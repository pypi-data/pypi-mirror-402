import click
import sys
import itertools
import time
import math

from datetime import datetime
from urllib.parse import urlparse, parse_qs

from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table

from depoc.objects.base import DepocObject

console = Console()


def _format_transaction_inventory(
        obj: DepocObject,
        update: bool = False,
    ):

    date = datetime.fromisoformat(obj.date)
    obj.date = date.strftime('%Y-%m-%d %H:%M:%S')

    table = Table(
        show_header=True,
        show_footer=True,
        box=None,
        expand=True,
        title=f'{obj.inventory.product}',
        caption=f'{obj.date}',
        title_justify='right',
        caption_justify='center',
    )

    table.add_column('', justify='left', no_wrap=True)
    table.add_column('', justify='left', no_wrap=True)

    data = obj.to_dict()
    data.pop('id')
    data.pop('type')
    data.pop('description')
    data.pop('date')

    for k, v in data.items():
        k = k.replace('_', ' ').title()
        
        if isinstance(v, DepocObject):
            v = v.id

        table.add_row(f'{k}: ', f'{v}')

    panel_title = f'[{obj.quantity}] {obj.type.upper()}'

    if update:
        style = 'green'
        panel_title = f'[bold][green]{panel_title}'
        subtitle = f'[green]{obj.id}'
    else:
        style = 'none'
        panel_title = f'[bold]{panel_title}'
        subtitle = f'[blue]{obj.id}'

    description = Table(
        show_header=False,
        show_footer=True,
        box=None,
        expand=True,
        title=obj.description,
        title_justify='center',
    )
    description.add_column('', justify='left', no_wrap=True)
    
    group = Group(table, description)

    profile = Panel(
        group,
        title=panel_title,
        title_align='left', 
        subtitle=subtitle,
        subtitle_align='left',
        style=style
    )

    console.print(profile)


def _format_inventory(
        obj: DepocObject,
        update: bool = False,
    ):

    table = Table(
        show_header=True,
        show_footer=True,
        box=None,
        expand=True,
        title=f'Inventory',
        title_justify='right',
    )

    table.add_column('', justify='left', no_wrap=True)
    table.add_column('', justify='left', no_wrap=True)

    data = obj.to_dict()
    data.pop('id')

    for k, v in data.items():
        k = k.title()
        
        if isinstance(v, DepocObject):
            v = v.id

        table.add_row(f'{k}: ', f'{v}')

    name = f'[{obj.quantity}] {obj.product.name.upper()}'

    if update:
        style = 'green'
        panel_title = f'[bold][green]{name}'
        subtitle = f'[green]{obj.id}'
    else:
        style = 'none'
        panel_title = f'[bold]{name}'
        subtitle = f'[blue]{obj.id}'

    profile = Panel(
        table,
        title=panel_title,
        title_align='left', 
        subtitle=subtitle,
        subtitle_align='left',
        style=style
    )

    console.print(profile)


def _format_product(
        obj: DepocObject,
        update: bool = False,
    ):

    table = Table(
        show_header=True,
        show_footer=True,
        box=None,
        expand=True,
        title=obj.retail_price,
        title_justify='right',
        caption=f'{str(obj.stock)}',
        caption_justify='right'
    )

    table.add_column('', justify='left', no_wrap=True)
    table.add_column('', justify='left', no_wrap=True)

    data = obj.to_dict()
    data.pop('id')
    data.pop('name')
    data.pop('is_active')

    for k, v in data.items():
        k = k.replace('_', ' ').title()
        k = k.replace('Is ', '')

        if isinstance(v, DepocObject):
            v = f'@{v.username}'
        
        if v and obj.is_active:
            table.add_row(f'{k}: ', f'{v}')

    name = obj.name.upper()

    if update:
        style = 'green'
        panel_title = f'[bold][green]{name}'
        subtitle = f'[green]{obj.id}'
    elif not obj.is_active:
        style = 'grey50'
        panel_title = f'[bold][grey0]{name}'
        subtitle = f'[grey0]Deactivated • {obj.id}'
    else:
        style = 'none'
        panel_title = f'[bold]{name}'
        subtitle = f'[blue]{obj.id}'

    profile = Panel(
        table,
        title=panel_title,
        title_align='left', 
        subtitle=subtitle,
        subtitle_align='left',
        style=style
    )

    console.print(profile)


def _format_member(
        obj: DepocObject,
        title: str,
        update: bool = False,
    ):

    if obj.credential:
        title = f'@{obj.credential.username}'
    else:
        title = ''

    table = Table(
        show_header=True,
        show_footer=True,
        box=None,
        expand=True,
        title=title,
        title_justify='right',
    )

    table.add_column('', justify='left', no_wrap=True)
    table.add_column('', justify='left', no_wrap=True)

    data = obj.to_dict()
    data.pop('id')

    for k, v in data.items():
        k = k.replace('_', ' ').title()
        k = k.replace('Is ', '')
        k = k.upper() if k in ('Cpf', 'Cnpj', 'Ie', 'Im') else k
        k = 'Birthday' if k == 'Date Of Birth' else k

        if isinstance(v, DepocObject):
            v = f'@{v.username}'
        
        if v and obj.is_active:
            table.add_row(f'{k}: ', f'{v}')

    if update:
        style = 'green'
        panel_title = f'[bold][green]{obj.name}'
        subtitle = f'[green]{obj.id}'
    elif not obj.is_active:
        style = 'grey50'
        panel_title = f'[bold][grey0]{obj.name}'
        subtitle = f'[grey0]Deactivated • {obj.id}'
    else:
        style = 'none'
        panel_title = f'[bold]{obj.name}'
        subtitle = f'[blue]{obj.id}'

    profile = Panel(
        table,
        title=panel_title,
        title_align='left', 
        subtitle=subtitle,
        subtitle_align='left',
        style=style
    )

    console.print(profile)


def _format_business(
        response: DepocObject,
        title: str,
        update: bool = False,
    ):

    table = Table(
        show_header=True,
        show_footer=True,
        box=None,
        expand=True,
        title=response.cnpj,
        title_justify='right',
        caption=response.trade_name,
        caption_justify='right'
    )

    table.add_column('', justify='left', no_wrap=True)
    table.add_column('', justify='left', no_wrap=True)

    data = response.to_dict()
    data.pop('id')

    for k, v in data.items():
        k = k.replace('_', ' ').title()
        k = k.replace('Is ', '')
        k = k.upper() if k in ('Cpf', 'Cnpj', 'Ie', 'Im') else k
        
        if v and response.is_active:
            table.add_row(f'{k}: ', f'{v}')

    if update:
        style = 'green'
        panel_title = f'[bold][green]{title}'
        subtitle = f'[green]{response.id}'
    elif not response.is_active:
        style = 'grey50'
        panel_title = f'[bold][grey0]{title}'
        subtitle = f'[grey0]Deactivated • {response.id}'
    else:
        style = 'none'
        panel_title = f'[bold]{title}'
        subtitle = f'[blue]{response.id}'

    profile = Panel(
        table,
        title=panel_title,
        title_align='left', 
        subtitle=subtitle,
        subtitle_align='left',
        style=style
    )

    console.print(profile)


def _format_bank(obj, update: bool = False):
    table = Table(
        show_header=False,
        show_footer=True,
        box=None,
        expand=True,
        caption=f'{obj.id}',
        caption_justify='left'
        )
    
    table.add_column('', justify='left', no_wrap=True)
    table.add_column('', justify='right', no_wrap=True)
    balance = float(obj.balance)
    table.add_row(f'', f'[bold]R${balance:,.2f}')

    if update:
        border_style = 'green'
    elif not obj.is_active:
        border_style = 'red'
    else:
        border_style = 'none'

    panel = Panel(
        table,
        title=f'[bold]{obj.name.upper()}',
        title_align='left',
        border_style=border_style,
    )

    console.print(panel)


def _format_category(obj, highlight: bool = False):
    table = Table(
        show_header=True,
        show_footer=True,
        box=None,
        expand=True,
        )
    
    table.add_column('', justify='left', no_wrap=True)
    table.add_column('', justify='right', no_wrap=True)

    table.add_row(obj.name, obj.id)

    border_style = 'none'
    style = 'none'

    if highlight:
        border_style='green'
        style='green'

    profile = Panel(
        table,
        title_align='left',
        subtitle_align='left',
        border_style=border_style,
        style=style,
    )
    console.print(profile)


def _format_transactions(
        obj: DepocObject,
        title: str,
        update: bool = False,
        detail: bool = False
    ):

    timestamp = datetime.fromisoformat(obj.timestamp)
    obj.timestamp = timestamp.strftime('%Y-%m-%d %H:%M:%S')

    table = Table(
        show_header=True,
        show_footer=True,
        box=None,
        expand=True,
        title=f'R${float(obj.amount):,.2f}',
        caption=obj.timestamp,
        title_justify='right',
    )

    table.add_column('', justify='left', no_wrap=True)
    table.add_column('', justify='right', no_wrap=True)

    data = obj.to_dict()
    data.pop('id', None)
    data.pop('description', None)
    data.pop('timestamp', None)
    data.pop('type', None)
    data.pop('account', None)
    data.pop('amount', None)

    if not detail:
        data.pop('operator', None)
        data.pop('linked', None)

    for k, v in data.items():
        k = k.replace('_', ' ').title()
        k = k.replace('Is ', '')
        k = k.upper() if k in ('Cpf', 'Cnpj', 'Ie', 'Im') else k

        if isinstance(v, DepocObject):
            if hasattr(v, 'name'):
                v = v.name
        
        if v:
            table.add_row(f'{k}: ', f'{v}')
    
    description = Table(
        show_header=False,
        show_footer=True,
        box=None,
        expand=True,
        title=obj.description,
        title_justify='center',
    )
    description.add_column('', justify='left', no_wrap=True)
    
    group = Group(table, description)

    style = 'none'
    panel_title = f'{title}'
    subtitle = f'[bold]{obj.id}'
    border_style = 'none'

    if update:
        style = 'green'
        panel_title = f'[bold][green]{title}'
        subtitle = f'[green]{obj.id}'
        border_style = 'none'
    elif obj.type == 'credit':
        border_style = 'green'
    elif obj.type == 'debit':
        border_style = 'red'

    profile = Panel(
        group,
        title=panel_title,
        title_align='left', 
        subtitle=subtitle,
        subtitle_align='left',
        style=style,
        border_style=border_style,
    )

    console.print(profile)


def _format_payments(
        obj: DepocObject,
        title: str,
        update: bool = False,
        detail: bool = False
    ):

    table_title = f'[bold]R${float(obj.outstanding_balance):,.2f}'

    table = Table(
        show_header=True,
        show_footer=True,
        box=None,
        expand=True,
        title=table_title,
        caption=f'{obj.due_at}',
        title_justify='right',
        caption_justify='center'
    )

    table.add_column('', justify='left', no_wrap=True)
    table.add_column('', justify='left', no_wrap=True)

    data = obj.to_dict()
    data.pop('id', None)
    data.pop('notes', None)
    data.pop('contact', None)
    data.pop('payment_type', None)

    if not detail:
        data.pop('status', None)
        data.pop('due_at', None)
        data.pop('updated_at', None)
        data.pop('payment_method', None)
        data.pop('recurrence', None)
        data.pop('reference', None)

    for k, v in data.items():
        if k in 'updated_at':
            v = v[:10] if v is not None else 'null'

        k = k.replace('_', ' ').title()
        k = k.replace('Is ', '')
        k = k.upper() if k in ('Cpf', 'Cnpj', 'Ie', 'Im') else k
        
        if v:
            table.add_row(f'{k}: ', f'{v}')
    
    notes = Table(
        show_header=False,
        show_footer=True,
        box=None,
        expand=True,
        title=obj.notes,
        title_justify='center',
    )
    notes.add_column('', justify='left', no_wrap=True)
    
    group = Group(table, notes)

    style = 'none'
    panel_title = f'[bold]{title}'
    subtitle = f'[bold][blue]{obj.id}'
    border_style = 'none'

    if update:
        style = 'green'
        panel_title = f'[bold][green]{title}'
        subtitle = f'[green]{obj.id}'
        border_style = 'none'
    elif obj.status == 'overdue':
        style = 'none'
        panel_title = f'[bold]{title}'
        subtitle = f'[bold]{obj.id}'
        border_style = 'red'
    elif obj.status == 'paid':
        style = 'none'
        panel_title = f'[bold]{title}'
        subtitle = f'[bold]{obj.id}'
        border_style = 'green'

    profile = Panel(
        group,
        title=panel_title,
        title_align='left', 
        subtitle=subtitle,
        subtitle_align='left',
        style=style,
        border_style=border_style,
    )

    console.print(profile)


def _format_contact(
        obj: DepocObject,
        title: str,
        update: bool = False,
    ):

    if hasattr(obj, 'alias'):
        table_title = obj.alias
        caption = 'customer'
    elif hasattr(obj, 'trade_name'):
        table_title = obj.trade_name
        caption = 'supplier'

    table = Table(
        show_header=True,
        show_footer=True,
        box=None,
        expand=True,
        title=table_title,
        title_justify='right',
        caption=caption,
        caption_justify='right'
    )

    table.add_column('', justify='left', no_wrap=True)
    table.add_column('', justify='left', no_wrap=True)

    data = obj.to_dict()
    data.pop('id', None)
    data.pop('name', None)
    data.pop('alias', None)
    data.pop('legal_name', None)
    data.pop('trade_name', None)
    data.pop('notes', None)

    for k, v in data.items():
        if k in ('last_login', 'date_joined', 'created_at'):
            v = v[:10] if v is not None else 'null'

        k = k.replace('_', ' ').title()
        k = k.replace('Is ', '')
        k = k.upper() if k in ('Cpf', 'Cnpj', 'Ie', 'Im') else k
        
        if v and obj.is_active:
            table.add_row(f'{k}: ', f'{v}')
    
    group = Group(table)

    if obj.notes:
        notes = Table(
            show_header=False,
            show_footer=True,
            box=None,
            expand=True,
            title=obj.notes,
            title_justify='center',
        )
        notes.add_column('', justify='left', no_wrap=True)
        group = Group(table, notes)

    if update:
        style = 'green'
        panel_title = f'[bold][green]{title}'
        subtitle = f'[green]{obj.id}'
    elif not obj.is_active:
        style = 'bright_red'
        panel_title = f'[bold][bright_red]{title}'
        subtitle = f'[bright_red]{obj.id}'
    else:
        style = 'none'
        panel_title = f'[bold]{title}'
        subtitle = f'[blue]{obj.id}'

    profile = Panel(
        group,
        title=panel_title,
        title_align='left', 
        subtitle=subtitle,
        subtitle_align='left',
        style=style
    )

    console.print(profile)


def _format_profile(
        obj: DepocObject,
        title: str,
        columns: int = 2,
        update: bool = False,
        delete: bool = False,
    ):
    table = Table(show_header=True, show_footer=True, box=None, expand=True)

    for _ in range(columns):
        table.add_column('', justify='left', no_wrap=True)

    data = obj.to_dict()

    for k, v in data.items():
        if k in ('last_login', 'date_joined'):
            v = v[:10] if v is not None else 'null'

        k = k.replace('_', ' ').title()
        k = k.replace('Is ', '')
        k = k.upper() if k == 'Id' else k
        
        table.add_row(f'{k}: ', f'{v}')

    if update:
        style = 'green'
    elif delete:
        style = 'red'
    else:
        style = 'none'

    profile = Panel(table, title=f'[bold]{title}', title_align='left', style=style)

    console = Console()
    console.print(profile)


def spinner(text: str = 'Deleting') -> None:
    spinner_cycle = itertools.cycle(['-', '\\', '|', '/'])
    for _ in range(20):
        sys.stdout.write(f'\r{text} {next(spinner_cycle)} ')
        sys.stdout.flush()
        time.sleep(0.1)
    click.echo('')


def page_summary(response: DepocObject):
    total_pages = math.ceil(response.count / 50)
    results_count = len(response.results)
    current_page = 0

    last_page = response.previous and not response.next

    if response.next:
        query = urlparse(response.next).query
        params = parse_qs(query)
        next_page = int(params.get('page', [1])[0])
        current_page = next_page - 1
    elif last_page:
        current_page = total_pages
    elif total_pages != 0 and total_pages <= 50:
        current_page = 1

    message = (
        f'\n[Page {current_page}/{total_pages}] '
        f'Showing {results_count} results (Total: {response.count})\n'
        f'Inactive results are not shown\n'
    )

    click.echo(message)
