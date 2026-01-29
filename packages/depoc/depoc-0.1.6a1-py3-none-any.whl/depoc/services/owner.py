from depoc.resources.methods import Retrieve, Update
from depoc.objects.owner import OwnerObject


class Owner(Retrieve[OwnerObject], Update[OwnerObject]):
    obj = OwnerObject
    endpoint = 'owner'
    label = 'owner'
