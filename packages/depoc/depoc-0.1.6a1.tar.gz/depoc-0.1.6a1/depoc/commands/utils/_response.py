import click

from typing import Any

from depoc.objects.base import DepocObject
from depoc.utils._error import APIError


def _handle_response(
        service: Any,
        data: dict[str, Any] | None = None,
        resource_id: str | None = None,
        **params,
    ) -> DepocObject | None:
    '''
    Handles the response for a service method call.

    The `service` argument should be a method of a
    resourcein the DepocClient instance.

    Examples of valid service methods:
    - `client.customer.create` 
    - `client.receivable.all`
    '''
    try:
        if data and resource_id:
            response = service(data, resource_id, **params)
        elif data:
            response = service(data)
        elif resource_id:
            response = service(resource_id, **params)
        else:
            response = service(**params)

        return response
    
    except APIError as e:
        click.echo(str(e))
    return None
