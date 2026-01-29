from .base import DepocObject


class OwnerObject(DepocObject):
    ''' Represents an owner resource '''

    id: str
    ''' Unique identifier of the owner. '''
    name: str
    ''' Full name of the owner. '''
    email: str
    ''' Owner's email address. '''
    phone: str
    ''' Owner's phone number. '''
