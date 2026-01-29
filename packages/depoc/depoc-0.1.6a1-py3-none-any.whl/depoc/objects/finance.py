from .base import DepocObject


class FinancialAccountObject(DepocObject):
    '''Represents a financial account with balance and status.'''

    id: str
    '''Unique identifier for the account.'''

    name: str
    '''Name of the financial account.'''

    balance: str
    '''Current balance of the account.'''

    created_at: str
    '''Timestamp of when the account was created.'''

    is_active: bool
    '''Indicates if the account is active.'''


class FinancialCategoryObject(DepocObject):
    '''Represents a category for financial transactions.'''

    id: str
    '''Unique identifier for the category.'''

    name: str
    '''Name of the financial category.'''

    parent: str
    '''ID of the parent category, if any.'''

    is_active: str
    '''Indicates if the category is active.'''


class FinancialTransactionObject(DepocObject):
    '''Represents a financial transaction record.'''

    id: str
    '''Unique identifier for the transaction.'''

    category: dict
    '''ID of the associated financial category.'''

    operator: dict
    '''ID of the user or entity that performed the transaction.'''

    account: dict
    '''ID of the account involved in the transaction.'''

    contact: dict
    '''ID of the related contact or client.'''

    payment: str
    '''ID of the related Payment (payable or receivable).'''

    linked: str
    '''ID of any linked transaction.'''

    amount: float
    '''Transaction amount.'''

    description: str
    '''Detailed description of the transaction.'''

    type: str
    '''Type of transaction (e.g., credit, debit).'''

    timestamp: str
    '''Date and time when the transaction occurred.'''
