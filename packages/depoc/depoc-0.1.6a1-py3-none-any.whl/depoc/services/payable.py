from depoc.resources.methods import Finder, Create, Retrieve, Update, Delete
from depoc.objects.payment import PaymentObject, PaymentSettleObject


class Payable(
    Finder[PaymentObject],
    Create[PaymentObject],
    Retrieve[PaymentObject],
    Update[PaymentObject],
    Delete[PaymentObject],
):
    obj = PaymentObject
    endpoint = 'payables'
    label = 'payment'


class PayableSettle(
    Create[PaymentSettleObject]
):
    obj = PaymentSettleObject
    endpoint = 'payables/<id>/settle'
    label = 'transaction'
