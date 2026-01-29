from depoc.objects.base import DepocObject


class AccountObject(DepocObject):
    ''' Represents the current user account resource '''

    id: str
    ''' Unique identifier of the account. '''
    name: str
    ''' Full name of the user. '''
    email: str
    ''' User's email address. '''
    username: str
    ''' Unique username of the user. '''
