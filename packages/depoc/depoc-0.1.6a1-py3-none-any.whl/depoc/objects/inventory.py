from .base import DepocObject


class InventoryObject(DepocObject):
    '''
    Represents the inventory details of a product,
    including quantities and location.
    '''

    id: str
    '''
    Unique identifier for the inventory record.
    '''
    quantity: int
    '''
    Total available quantity of the product in stock.
    '''
    reserved: int
    '''
    Quantity of the product reserved for pending orders or other commitments.
    '''
    location: str
    '''
    Physical or logical location of the inventory (e.g., warehouse, store).
    '''
    product: dict
    '''
    Dictionary containing detailed information about the associated product.
    '''


class InventoryTransctionObject(DepocObject):
    '''
    Represents a transaction involving inventory, including details on type, quantity, and pricing.
    '''
    
    id: str
    '''
    Unique identifier for the inventory transaction.
    '''
    type: str
    '''
    Type of transaction (e.g., 'purchase', 'sale', 'return', 'adjustment').
    '''
    date: str
    '''
    Date when the transaction occurred.
    '''
    quantity: int
    '''
    Number of units involved in the transaction.
    '''
    unit_cost: float
    '''
    Cost per unit for the transaction.
    '''
    unit_price: float
    '''
    Selling price per unit, if applicable.
    '''
    description: str
    '''
    Additional details or notes about the transaction.
    '''
    inventory: dict
    '''
    Dictionary containing details of the related inventory record.
    '''

