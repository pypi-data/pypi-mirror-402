from depoc.resources.methods import Update, Delete
from depoc.objects.account import AccountObject


class Account(Update[AccountObject], Delete[AccountObject]):
    obj = AccountObject
    endpoint = 'accounts'
    label = 'user'
