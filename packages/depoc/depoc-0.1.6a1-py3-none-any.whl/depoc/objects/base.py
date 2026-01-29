import json

from typing import Any


class DepocObjectEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, DepocObject):
            return o.to_dict()
        return super().default(o)


class DepocObject:
    # Paginator attributes
    count: int
    ''' Total number of results available. '''
    results: list
    ''' List containing the current page of results. '''
    next: str
    ''' URL to the next page of results, if available. '''
    previous: str
    ''' URL to the previous page of results, if available. '''

    def __init__(self, data: dict[str, Any] | None = None):
        self._values: dict[str, Any] = {}
        self._changes: set = set()
        if data:
            self.refresh_from(data)

    def refresh_from(self, data: dict[str, Any]) -> None:
        self._changes.clear()
        for key, value in data.items():
            if isinstance(value, dict):
                self._values[key] = DepocObject(value)
            elif isinstance(value, list):
                self._values[key] = [DepocObject(item) for item in value]
            else:
                self._values[key] = value

    def __setattr__(self, key, value):
        if key.startswith('_'):
            return super().__setattr__(key, value)
        else:
            self._changes.add(key)
            if isinstance(value, dict):
                self._values[key] = DepocObject(value)
            elif isinstance(value, list):
                self._values[key] = [DepocObject(item) for item in value]
            else:
                self._values[key] = value

    def __getattr__(self, name):
        try:
            return self._values[name]
        except KeyError as e:
            message = f"'{type(self).__name__}' object has no attribute '{name}'"
            raise AttributeError(message) from e

    def __repr__(self):
        id_str = f" id={self.id}" if hasattr(self, 'id') else ""
        return f"<{type(self).__name__}{id_str}>"
    
    def __dir__(self):
        return list(self._values.keys()) + super().__dir__()

    def __str__(self) -> str:
        return f'DepocObject({json.dumps(
            self._values,
            cls=DepocObjectEncoder,
            ensure_ascii=False,
            indent=2,
        )})'

    def to_dict(self) -> dict[str, Any]:
        return {key: value for key, value in self._values.items()}
    
    @property
    def changes(self):
        return {k: self._values[k] for k in self._changes}
