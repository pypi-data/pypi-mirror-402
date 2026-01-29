from .base import DepocObject


class SupplierObject(DepocObject):
    '''
    Represents a supplier with identification, contact details,
    registration numbers, and status information.
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
    code: str
    ''' Unique internal supplier code. '''
    phone: str
    ''' Primary contact phone number. '''
    email: str
    ''' Contact email address. '''
    postcode: str
    ''' Postal code of the supplier's address. '''
    city: str
    ''' City where the supplier resides. '''
    state: str
    ''' State where the supplier resides. '''
    address: str
    ''' Full residential address of the supplier. '''
    notes: str
    ''' Additional notes or comments about the supplier. '''
    is_active: bool
    ''' Indicates if the supplier account is currently active. '''
    created_at: str
    ''' Timestamp of when the supplier record was created. '''
    updated_at: str
    ''' Timestamp of when the supplier record was last updated. '''
