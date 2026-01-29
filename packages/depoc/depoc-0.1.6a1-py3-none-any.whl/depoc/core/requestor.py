import depoc
import requests

from typing import Literal, Any

from depoc.utils import _handle_response


class Requestor(object):
    def __init__(self):
        self._session = requests.Session()
        self._session.headers.update({
            'User-Agent': 'depoc/0.0.3 (Python)',
            'Content-Type': 'application/json',
        })

    def request(
        self,
        method: Literal['GET', 'POST', 'PATCH', 'PUT', 'DELETE'],
        endpoint: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        url = f'{depoc.BASE_URL}/{endpoint}'
        auth = {'Authorization': f'Bearer {depoc.token}'}
        
        try:
            response = self._session.request(
                method,
                url,
                json=params,
                headers=auth,
            )
            return _handle_response(response)

        except requests.exceptions.RequestException as e:
            raise Exception(str(e)) from e
        except requests.exceptions.HTTPError as e:
            raise Exception(str(e)) from e
