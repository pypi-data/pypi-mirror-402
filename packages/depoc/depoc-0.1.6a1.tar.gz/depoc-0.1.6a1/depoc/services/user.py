from depoc.resources.methods import Retrieve
from depoc.objects.user import UserObject


class User(Retrieve[UserObject]):
    obj = UserObject
    endpoint = 'me'
    label = 'user'
