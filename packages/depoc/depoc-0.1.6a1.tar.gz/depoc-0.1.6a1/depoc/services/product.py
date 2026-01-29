from depoc.resources.methods import Finder, Create, Retrieve, Update, Delete
from depoc.objects.product import (
    ProductObject,
    ProductCategoryObject,
    ProductCostObject,
)


class Product(
    Finder[ProductObject],
    Create[ProductObject],
    Retrieve[ProductObject],
    Update[ProductObject],
    Delete[ProductObject],
):
    obj = ProductObject
    endpoint = 'products'
    label = 'product'


class ProductCategory(
    Finder[ProductCategoryObject],
    Create[ProductCategoryObject],
    Retrieve[ProductCategoryObject],
    Update[ProductCategoryObject],
    Delete[ProductCategoryObject],
):
    obj = ProductCategoryObject
    endpoint = 'products/categories'
    label = 'category'


class ProductCost(
    Finder[ProductCostObject],
    Create[ProductCostObject],
    Retrieve[ProductCostObject],
    Update[ProductCostObject],
    Delete[ProductCostObject],
):
    obj = ProductCostObject
    endpoint = 'products/<id>/costs'
    label = 'cost'
