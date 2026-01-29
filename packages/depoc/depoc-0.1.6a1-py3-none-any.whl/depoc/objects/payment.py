from .base import DepocObject


class PaymentObject(DepocObject):
    '''
    Represents a payment record, including details about
    amounts, dates, status, and payment method.
    '''
    
    id: str
    '''
    Unique identifier for the payment record.
    '''
    contact: str
    '''
    Identifier for the contact or entity associated with the payment.
    '''
    category: str
    '''
    Category ID of the payment.
    '''
    issued_at: str
    '''
    Date when the payment was issued.
    '''
    due_at: str
    '''
    Due date for the payment.
    '''
    paid_at: str
    '''
    Date when the payment was completed.
    '''
    updated_at: str
    '''
    Timestamp for the last update to the payment record.
    '''
    total_amount: float
    '''
    Total amount due for the payment.
    '''
    amount_paid: float
    '''
    Amount that has been paid so far.
    '''
    outstanding_balance: float
    '''
    Remaining unpaid balance.
    '''
    payment_type: str
    '''
    Type of payment ('payable', 'receivable').
    '''
    payment_method: str
    '''
    Method used for the payment (e.g., 'credit card', 'bank transfer').
    '''
    status: str
    '''
    Current status of the payment (e.g., 'pending', 'paid', 'overdue').
    '''
    recurrence: str
    '''
    Frequency of the recurring payment (e.g., 'monthly', 'weekly').
    '''
    installment_count: int
    '''
    Number of installments for the payment, if applicable.
    '''
    due_weekday: str
    '''
    Day of the week when payment is due (e.g., 'Monday').
    '''
    due_day_of_month: str
    '''
    Specific day of the month when payment is due.
    '''
    reference: str
    '''
    External reference number for the payment.
    '''
    notes: str
    '''
    Additional notes or comments related to the payment.
    '''


class PaymentSettleObject(DepocObject):
    '''
    Represents the settlement details of a payment,
    including amount and accounts involved.
    '''

    amount: str
    '''
    Amount to be settled in the payment.
    '''
    accounts: str
    '''
    Account details used for settling the payment.
    '''
