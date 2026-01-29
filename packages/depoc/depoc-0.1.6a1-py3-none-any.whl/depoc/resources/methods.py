from typing import Any

from .base import T, APIResource


class Finder(APIResource[T]):
    @classmethod
    def filter(
            cls,
            search: str | None = None,
            date: str | None = None,
            start_date: str | None = None,
            end_date: str | None = None,
            limit: int | None = None,
            page: int | None = None,
        ):
        endpoint = f'{cls.endpoint}?'

        if search:
            endpoint += f'&search={search}'
        
        if date:
            endpoint += f'&date={date}'

        if start_date and end_date:
            endpoint += f'&start_date={start_date}&end_date={end_date}'

        if page:
            endpoint += f'&page={page}'

        response = cls.requestor.request('GET', endpoint)
        return cls._paginate(response, limit)


class Create(APIResource[T]):
    @classmethod
    def create(cls, params: dict[str, Any], resource_id: str | None = None) -> T:
        endpoint = cls.endpoint
        if '<id>' in endpoint and resource_id:
            endpoint = cls.endpoint.replace('<id>', resource_id)

        response = cls.requestor.request('POST', endpoint, params)
        return cls._convert_to_object(response)


class Retrieve(APIResource[T]):
    @classmethod
    def get(
            cls, 
            resource_id: str | None = None,
            resource_id2: str | None = None,
        ) -> T:
        endpoint = cls.endpoint

        endpoint = f'{endpoint}/{resource_id}' if resource_id else endpoint

        if '<id>' in endpoint and resource_id:
            endpoint = cls.endpoint.replace('<id>', resource_id)
            if resource_id2:
                endpoint += f'/{resource_id2}'

        response = cls.requestor.request('GET', endpoint)
        return cls._convert_to_object(response)
    
    @classmethod
    def all(
        cls,
        resource_id: str | None = None,
        *,
        limit: int | None = None, 
        page: int | None = None,
    ) -> T:
        endpoint = cls.endpoint
        if '<id>' in endpoint and resource_id:
            endpoint = cls.endpoint.replace('<id>', resource_id)
            
        endpoint = f'{endpoint}?page={page}' if page else endpoint
        response = cls.requestor.request('GET', endpoint)
        return cls._paginate(response, limit)


class Update(APIResource[T]):
    @classmethod
    def update(
        cls,
        params: dict[str, Any],
        resource_id: str | None = None,
        resource_id2: str | None = None,
    ) -> T:
        endpoint = cls.endpoint

        endpoint = f'{endpoint}/{resource_id}' if resource_id else endpoint

        if '<id>' in endpoint and resource_id:
            endpoint = cls.endpoint.replace('<id>', resource_id)
            if resource_id2:
                endpoint += f'/{resource_id2}'

        response = cls.requestor.request('PATCH', endpoint, params)
        return cls._convert_to_object(response)


class Delete(APIResource[T]):
    @classmethod
    def delete(
            cls,
            resource_id: str | None = None,
            resource_id2: str | None = None,
        ) -> T:
        endpoint = cls.endpoint

        endpoint = f'{endpoint}/{resource_id}' if resource_id else endpoint

        if '<id>' in endpoint and resource_id and resource_id2:
            endpoint = cls.endpoint.replace('<id>', resource_id)
            endpoint += f'/{resource_id2}'

        response = cls.requestor.request('DELETE', endpoint)
        return cls._convert_to_object(response)
