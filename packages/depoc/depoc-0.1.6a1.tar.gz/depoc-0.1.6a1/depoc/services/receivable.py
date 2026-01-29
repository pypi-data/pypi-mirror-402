from depoc.resources.methods import Finder, Create, Retrieve, Update, Delete
from depoc.objects.payment import PaymentObject, PaymentSettleObject


class Receivable(
    Finder[PaymentObject],
    Create[PaymentObject],
    Retrieve[PaymentObject],
    Update[PaymentObject],
    Delete[PaymentObject],
):
    obj = PaymentObject
    endpoint = 'receivables'
    label = 'payment'


class ReceivableSettle(
    Create[PaymentSettleObject]
):
    obj = PaymentSettleObject
    endpoint = 'receivables/<id>/settle'
    label = 'transaction'
