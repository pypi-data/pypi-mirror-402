from .base import DepocObject


class MemberObject(DepocObject):
    ''' Represents a member of the business '''

    id: str
    ''' Unique identifier of the member. '''
    name: str
    ''' Full name of the member. '''
    email: str
    ''' Member's email address. '''
    phone: str
    ''' Member's phone number. '''
    cpf: str
    ''' Brazilian individual taxpayer registry identification (CPF). '''
    date_of_birth: str
    ''' Member's date of birth in YYYY-MM-DD format. '''
    role: str
    ''' Position or job title of the member within the business. '''
    hire_date: str
    ''' Date the member was hired, in YYYY-MM-DD format. '''
    salary: float
    ''' Member's salary. '''
    has_access: bool
    ''' Indicates if the member has system access. '''
    is_active: bool
    ''' Indicates if the member is currently active in the organization. '''
    credential: dict
    ''' Access credentials. '''
