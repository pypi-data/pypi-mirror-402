from depoc.resources.methods import Create, Retrieve, Update, Delete
from depoc.objects.customer import CustomerObject


class Customer(
    Create[CustomerObject],
    Retrieve[CustomerObject],
    Update[CustomerObject],
    Delete[CustomerObject],
):
    obj = CustomerObject
    endpoint = 'contacts/customers'
    label = 'customer'
