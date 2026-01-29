from depoc.resources.methods import Create, Retrieve, Update, Delete
from depoc.objects.supplier import SupplierObject


class Supplier(
    Create[SupplierObject],
    Retrieve[SupplierObject],
    Update[SupplierObject],
    Delete[SupplierObject],
):
    obj = SupplierObject
    endpoint = 'contacts/suppliers'
    label = 'supplier'
