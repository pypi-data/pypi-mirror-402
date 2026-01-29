from depoc import Requestor


class Connection:
    def __init__(
            self,
            username: str,
            password: str,
    ):
        self.username = username
        self.password = password

    @property
    def token(self):
        return self._token(self.username, self.password)
    
    def _token(self, username: str, password: str) -> str | None:
        requestor = Requestor()
        params: dict[str, str] = {'username': username, 'password': password}
        response = requestor.request('POST', 'token', params=params)
        return response.get('access')
