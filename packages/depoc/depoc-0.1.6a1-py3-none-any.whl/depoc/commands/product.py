import depoc
import click
import time
import sys

from typing import Any

from .utils._response import _handle_response
from .utils._format import (
    spinner,
    page_summary, 
    _format_product,
    _format_category
)

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.console import group
from rich.table import Table


client = depoc.DepocClient()
console = Console()

@group()
def get_tables(tables: list):
    for table in tables:
        yield table


@click.group(invoke_without_command=True)
@click.pass_context
@click.option('-l', '--limit', default=50)
@click.option('-p', '--page', default=0)
def p(ctx, limit: int, page: int) -> None:
    ''' Manage products. '''
    if ctx.invoked_subcommand is None:
        service = client.products.all
        
        if response := _handle_response(service, limit=limit, page=page):
            page_summary(response)

            for obj in response.results:
               _format_product(obj)


@p.command
def create() -> None:
    ''' Create a new product. '''
    panel = Panel('[bold]+ ADD NEW PRODUCT')
    console.print(panel)

    data: dict[str, Any] = {}
    data.update({'name': Prompt.ask('Name', default=None)})
    console.rule('',style=None, align='left')
    data.update({'sku': Prompt.ask('SKU', default=None)}) 
    console.rule('',style=None, align='left')
    data.update({'barcode': Prompt.ask('Barcode', default=None)}) 
    console.rule('',style=None, align='left')
    data.update({'brand': Prompt.ask('Brand', default=None)}) 
    console.rule('',style=None, align='left')
    data.update({'category': Prompt.ask('Category', default=None)}) 
    console.rule('',style=None, align='left')
    data.update({'supplier': Prompt.ask('Supplier', default=[])}) 
    console.rule('',style=None, align='left')
    data.update({'cost_price': Prompt.ask('Cost $', default=None)}) 
    console.rule('',style=None, align='left')
    data.update({'retail_price': Prompt.ask('Retail Price $', default=None)}) 
    console.rule('',style=None, align='left')
    data.update(
        {'discounted_price': Prompt.ask('Discounted Price $', default=None)}
    ) 
    console.rule('',style=None, align='left')
    data.update({'unit': Prompt.ask('Unit', default=None)}) 
    console.rule('',style=None, align='left')
    data.update({'stock': Prompt.ask('Stock', default=None)}) 
    console.rule('',style=None, align='left')
    data.update({'is_available': Prompt.ask(        
        'Is Avaivable', choices=['True', 'False'])
    }) 
    console.rule('',style=None, align='left')
    data.update({'track_stock': Prompt.ask(        
        'Track Stock', choices=['True', 'False'])
    }) 
    console.rule('',style=None, align='left')

    service = client.products.create
    if response := _handle_response(service, data=data):
        _format_product(response)


@p.command
@click.argument('id')
def get(id) -> None:
    ''' Retrieve an specific product. '''
    service = client.products.get

    if obj := _handle_response(service, resource_id=id):
        _format_product(obj)


@p.command
@click.argument('id')
@click.option('-n', '--name')
@click.option('-s', '--sku')
@click.option('-b', '--brand')
@click.option('-bc', '--barcode')
@click.option('-c', '--category')
@click.option('-r', '--retail-price')
@click.option('-d', '--discounted-price')
@click.option('-sp', '--supplier')
@click.option('-u', '--unit')
@click.option('-a', '--is-available')
@click.option('-t', '--track-stock')
@click.option('--is-active')
def update(
    id,
    name,
    sku,
    barcode,
    brand,
    category,
    supplier,
    retail_price,
    discounted_price,
    unit,
    is_available,
    track_stock,
    is_active,
) -> None:
    ''' Update an specific product. '''
    if not any([
       name, sku, barcode, brand, category, supplier, retail_price,
       discounted_price, unit, is_available, track_stock, is_active
    ]):
        console.print('🚨 Specify a field to update')
        sys.exit()
    
    data: dict[str, Any] = {}
    data.update({'name': name}) if name else None
    data.update({'sku': sku}) if sku else None
    data.update({'barcode': barcode}) if barcode else None
    data.update({'brand': brand}) if brand else None
    data.update({'category': category}) if category else None
    data.update({'supplier': supplier}) if supplier else None
    data.update({'retail_price': retail_price}) if retail_price else None
    data.update({'discounted_price': discounted_price}) if discounted_price else None
    data.update({'unit': unit}) if unit else None
    data.update({'is_available': is_available}) if is_available else None
    data.update({'track_stock': track_stock}) if track_stock else None
    data.update({'is_active': is_active}) if is_active else None

    service = client.products.update

    if obj := _handle_response(service, data, resource_id=id):
        _format_product(obj, update=True)


@p.command
@click.argument('ids', nargs=-1)
def delete(ids: str) -> None:
    ''' Delete an specific customer. '''
    service = client.products.delete

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
            console.print('✅ Product inactivated')

@p.group(invoke_without_command=True)
@click.pass_context
@click.option('-l', '--limit', default=50)
@click.option('-p', '--page', default=0)
def category(ctx, limit: int, page: int) -> None:
    ''' Manage product categories '''
    if ctx.invoked_subcommand is None:
        service = client.product_categories.all

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

    service = client.product_categories.create
    if obj := _handle_response(service, data):
        _format_category(obj, highlight=True)


@category.command
@click.argument('id')
def get(id: str) -> None:
    ''' Retrieve an specific category '''
    service = client.product_categories.get
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

    service = client.product_categories.update

    if obj := _handle_response(service, data, id):
        _format_category(obj, highlight=True)

@category.command
@click.argument('ids', nargs=-1)
def delete(ids: str) -> None:
    ''' Delete a category '''
    service = client.product_categories.delete

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

@p.group()
def cost() -> None:
    ''' Manage product cost history. '''


@cost.command
@click.argument('id')
@click.option('-l', '--limit', default=50)
@click.option('-p', '--page', default=0)
def all(id: str, limit: int, page: int) -> None:
    ''' Retrieve all cost history of an specific product. '''
    service = client.product_cost.all

    if obj := _handle_response(service, resource_id=id, limit=limit, page=page):
        print(obj)


@cost.command
@click.option('-p', '--product', required=True)
@click.option('-c', '--cost', required=True)
def get(product: str, cost: str) -> None:
    ''' Retrieve an specific cost of an specific product. '''
    service = client.product_cost.get

    if obj := _handle_response(
        service,
        resource_id=product,
        resource_id2=cost
    ):
        print(obj)


@cost.command
@click.argument('product_id')
def create(product_id) -> None:
    ''' Create a product cost. '''
    panel = Panel('[bold]+ ADD NEW PRODUCT COST')
    console.print(panel)

    data: dict[str, Any] = {}
    data.update({'quantity': Prompt.ask('Quantity', default=None)})
    console.rule('',style=None, align='left')
    data.update({'effective_date': Prompt.ask('Effective date', default=None)})
    console.rule('',style=None, align='left')
    data.update({'cost_price': Prompt.ask('Cost price', default=None)})
    console.rule('',style=None, align='left')
    data.update({'retail_price': Prompt.ask('Retail rice', default=None)})
    console.rule('',style=None, align='left')
    data.update({'average_cost': Prompt.ask('Average cost', default=None)})
    console.rule('',style=None, align='left')
    data.update({'markup': Prompt.ask('Markup', default=None)})
    console.rule('',style=None, align='left')

    service = client.product_cost.create

    if obj := _handle_response(service, data, resource_id=product_id):
        print(obj)

@cost.command
@click.option('-p', '--product', required=True)
@click.option('-c', '--cost', required=True)
@click.option('-q', '--quantity')
@click.option('-e', '--effective-date')
@click.option('-cp', '--cost-price')
@click.option('-r', '--retail-price')
@click.option('-a', '--average-cost')
@click.option('-m', '--markup')
def update(
    product,
    cost,
    quantity,
    effective_date,
    cost_price,
    retail_price,
    average_cost,
    markup,
) -> None:
    ''' Update an specific cost. '''
    if not any([
       quantity, effective_date, cost_price, retail_price,
       average_cost, markup
    ]):
        console.print('🚨 Specify a field to update')
        sys.exit()

    data: dict[str, Any] = {}
    data.update({'quantity': quantity}) if quantity else None
    data.update({'effective_date': effective_date}) if effective_date else None
    data.update({'cost_price': cost_price}) if cost_price else None
    data.update({'retail_price': retail_price}) if retail_price else None
    data.update({'average_cost': average_cost}) if average_cost else None
    data.update({'markup': markup}) if markup else None

    service = client.product_cost.update

    if obj := _handle_response(
        service,
        data,
        resource_id=product,
        resource_id2=cost,
    ):
        print(obj)


@cost.command
@click.option('-p', '--product', required=True)
@click.option('-c', '--cost', required=True)
def delete(product: str, cost: str):
    ''' Delete an specific customer. '''
    service = client.product_cost.delete

    while True:
        prompt = click.style('Proceed to deletion? [y/n] ', fg='red')
        confirmation = input(prompt)
        if confirmation == 'n':
            sys.exit(0)
        elif confirmation == 'y':
            break

    if _handle_response(service, resource_id=product, resource_id2=cost):
        console.print('✅ Cost deleted')
