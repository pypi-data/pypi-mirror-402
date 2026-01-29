from .base import DepocObject


class CustomerObject(DepocObject):
    '''
    Represents a customer entity with personal details,
    contact information, and transaction history.
    '''

    id: str
    ''' Unique identifier for the customer '''
    name: str
    ''' Full name of the customer. '''
    alias: str
    ''' Preferred name or nickname of the customer. '''
    cpf: str
    ''' Brazilian individual taxpayer registry identification (CPF). '''
    gender: str
    ''' Gender of the customer. '''
    amount_spent: float
    ''' Total amount spent by the customer. '''
    number_of_orders: int
    ''' Total number of orders placed by the customer. '''
    code: str
    ''' Unique internal customer code. '''
    phone: str
    ''' Primary contact phone number. '''
    email: str
    ''' Contact email address. '''
    postcode: str
    ''' Postal code of the customer's address. '''
    city: str
    ''' City where the customer resides. '''
    state: str
    ''' State where the customer resides. '''
    address: str
    ''' Full residential address of the customer. '''
    notes: str
    ''' Additional notes or comments about the customer. '''
    is_active: bool
    ''' Indicates if the customer account is currently active. '''
    created_at: str
    ''' Timestamp of when the customer record was created. '''
    updated_at: str
    ''' Timestamp of when the customer record was last updated. '''
