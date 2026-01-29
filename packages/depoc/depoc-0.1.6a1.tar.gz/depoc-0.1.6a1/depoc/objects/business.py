from .base import DepocObject


class BusinessObject(DepocObject):
    '''
    Represents a business entity with identification,
    registration, and contact details.
    '''

    id: str
    ''' Unique identifier for the business. '''
    legal_name: str
    ''' Registered legal name of the business. '''
    trade_name: str
    ''' Commercial name used by the business. '''
    cnpj: str
    ''' Brazilian National Registry of Legal Entities (CNPJ). '''
    ie: str
    ''' State Registration Number (Inscrição Estadual). '''
    im: str
    ''' Municipal Registration Number (Inscrição Municipal). '''
    postcode: str
    ''' Postal code of the business address. '''
    city: str
    ''' City where the business is located. '''
    state: str
    ''' State where the business is registered. '''
    address: str
    ''' Full physical address of the business. '''
    phone: str
    ''' Primary contact phone number for the business. '''
    email: str
    ''' Primary contact email address for the business. '''
    is_active: bool
    ''' Indicates whether the business account is active. '''
