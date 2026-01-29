import depoc
import click

from .utils._response import _handle_response
from .utils._format import _format_contact, page_summary


client = depoc.DepocClient()


@click.group(invoke_without_command=True)
@click.pass_context
@click.argument('search', required=False)
@click.option('-l', '--limit', default=50)
@click.option('-p', '--page', default=0)
def contact(ctx, limit: int, page: int, search: str) -> None:
    ''' Contacts - retrieve all and filter. '''
    if ctx.invoked_subcommand is None:
        service = client.contacts.all
        response = _handle_response(service, limit=limit, page=page)

        if search:
            service = client.contacts.filter
            response = _handle_response(service, search=search, limit=limit)

        if response:
            page_summary(response)

            for obj in response.results:
                if hasattr(obj, 'customer'):
                    title = f'{obj.customer.name}'
                    obj = obj.customer
                elif hasattr(obj, 'supplier'):
                    title = f'{obj.supplier.legal_name}'
                    obj = obj.supplier
                
                _format_contact(obj, title)
