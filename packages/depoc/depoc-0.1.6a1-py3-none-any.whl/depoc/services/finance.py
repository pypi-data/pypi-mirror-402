from depoc.resources.methods import Finder, Create, Retrieve, Update, Delete
from depoc.objects.finance import (
    FinancialAccountObject,
    FinancialCategoryObject,
    FinancialTransactionObject,
)


class FinancialAccount(
    Create[FinancialAccountObject],
    Retrieve[FinancialAccountObject],
    Update[FinancialAccountObject],
    Delete[FinancialAccountObject],
):
    obj = FinancialAccountObject
    endpoint = 'finance/accounts'
    label = 'account'


class FinancialCategory(
    Create[FinancialCategoryObject],
    Retrieve[FinancialCategoryObject],
    Update[FinancialCategoryObject],
    Delete[FinancialCategoryObject],
):
    obj = FinancialCategoryObject
    endpoint = 'finance/categories'
    label = 'category'


class FinancialTransaction(
    Finder[FinancialTransactionObject],
    Create[FinancialTransactionObject],
    Retrieve[FinancialTransactionObject],
    Update[FinancialTransactionObject],
    Delete[FinancialTransactionObject],
):
    obj = FinancialTransactionObject
    endpoint = 'finance/transactions'
    label = 'transaction'
