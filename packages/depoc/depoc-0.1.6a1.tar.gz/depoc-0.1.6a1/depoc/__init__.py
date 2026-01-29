import json
import os

from depoc.core.requestor import Requestor
from depoc.core.client import DepocClient
from depoc.core.auth import Connection

from depoc.services.user import User
from depoc.services.owner import Owner
from depoc.services.account import Account
from depoc.services.business import Business
from depoc.services.customer import Customer
from depoc.services.supplier import Supplier

from appdirs import user_data_dir # type: ignore


# Constants
BASE_URL: str = 'https://api.depoc.com.br'
APP_NAME = 'depoc'


config_dir = user_data_dir(APP_NAME)
os.makedirs(config_dir, exist_ok=True)
token_path = os.path.join(config_dir, 'token.json')

token: str | None = None

try:
    with open(token_path, 'r') as f:
        data: dict = json.load(f)
        token = data.get('token')
except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
    pass
