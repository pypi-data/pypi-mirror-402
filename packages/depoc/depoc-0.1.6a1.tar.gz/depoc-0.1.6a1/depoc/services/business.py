from depoc.resources.methods import Create, Retrieve, Update, Delete
from depoc.objects.business import BusinessObject


class Business(
    Create[BusinessObject],
    Retrieve[BusinessObject],
    Update[BusinessObject],
    Delete[BusinessObject]
):
    obj = BusinessObject
    endpoint = 'business'
    label = 'business'
