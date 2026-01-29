from typing import Generic, TypeVar, Type, Any

from depoc.core.requestor import Requestor
from depoc.objects.base import DepocObject

T = TypeVar('T', bound=DepocObject)


class APIResource(Generic[T]):
    requestor: 'Requestor' = Requestor()
    endpoint: str
    obj: Type[T]
    label: str | None = None

    @classmethod
    def _convert_to_object(cls, data: dict[str, Any]) -> T:
        if not cls.obj:
            raise ValueError('Object class (`cls.obj`) must be defined.')
        if not cls.label:
            raise ValueError('Label class (`cls.label`) must be defined')
        return cls.obj(data.get(cls.label))

    @classmethod
    def _paginate(cls, data: dict[str, Any], limit: int | None = None) -> T:
        if not cls.obj:
            raise ValueError('Object class (`cls.obj`) must be defined.')
        
        if cls.label:
            # Extract nested resources by removing their labels 
            # (e.g., "customer", "product"). Simplifies access:
            # instead of customers.results[0].customer.id,
            # use customers.results[0].id
            results = data.get('results', [])
            extracted_results = [result.get(cls.label) for result in results]
            data['results'] = extracted_results[:limit]
        else:
            data['results'] = data['results'][:limit]

        return cls.obj(data)
