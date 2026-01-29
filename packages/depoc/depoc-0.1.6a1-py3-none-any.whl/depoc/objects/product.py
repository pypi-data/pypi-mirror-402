from .base import DepocObject


class ProductObject(DepocObject):
    '''
    Represents a product in the inventory system.
    Contains attributes related to identification,
    pricing, stock, and availability.
    '''

    id: str
    '''
    Unique identifier for the product.
    '''
    name: str
    '''
    Name of the product.
    '''
    sku: str
    '''
    Stock Keeping Unit, a unique code used for internal tracking.
    '''
    barcode: str
    '''
    Universal barcode assigned to the product for scanning purposes.
    '''
    brand: str
    '''
    Brand name of the product.
    '''
    category: str
    '''
    Category under which the product is classified.
    '''
    supplier: str
    '''
    Supplier or vendor providing the product.
    '''
    cost_price: float
    '''
    The cost price of the product.
    '''
    retail_price: float
    '''
    Regular selling price of the product.
    '''
    discounted_price: float
    '''
    Discounted selling price, if applicable.
    '''
    unit: str
    '''
    Unit of measurement for the product (e.g., piece, kg, liter).
    '''
    stock: int
    '''
    Current stock level of the product.
    '''
    is_available: bool
    '''
    Indicates whether the product is available for sale.
    '''
    track_stock: bool
    '''
    Indicates whether stock levels should be tracked.
    '''
    is_active: bool
    '''
    Indicates whether the product is active in the system.
    '''


class ProductCategoryObject(DepocObject):
    '''Represents a category for products.'''

    id: str
    '''Unique identifier for the category.'''

    name: str
    '''Name of the product category.'''

    parent: str
    '''ID of the parent category, if any.'''

    is_active: str
    '''Indicates if the category is active.'''


class ProductCostObject(DepocObject):
    '''
    Represents the cost details of a product over time,
    including pricing, quantity, and markup information.
    '''

    id: str
    '''
    Unique identifier for the product cost entry.
    '''
    product: str
    '''
    Identifier of the associated product.
    '''
    quantity: str
    '''
    Quantity of the product covered by this cost entry.
    '''
    effective_date: str
    '''
    Date when the cost becomes effective.
    '''
    cost_price: str
    '''
    The cost of the product at the effective date.
    '''
    retail_price: str
    '''
    The selling price of the product at the effective date.
    '''
    average_cost: str
    '''
    Average cost of the product based on historical purchases.
    '''
    markup: str
    '''
    Markup percentage applied to the cost price to determine the retail price.
    '''
