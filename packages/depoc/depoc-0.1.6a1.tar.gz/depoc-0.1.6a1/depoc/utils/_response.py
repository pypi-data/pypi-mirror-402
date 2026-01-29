from typing import Any
from requests import Response

from ._error import APIError


def _handle_response(response: Response) -> dict[str, Any]:
    status = response.status_code
    content_type = response.headers.get('Content-Type')
    not_json = content_type == 'text/html; charset=utf-8'

    if status == 404 and not_json:
        raise APIError('The requested resource was not found', 404)

    data: dict[str, Any] = response.json()

    if 'error' in data:
        error = data.get('error', {})
        message = error.get('message')
        status = error.get('status')
        details = error.get('details')
        raise APIError(message, status, details)
    
    return data
