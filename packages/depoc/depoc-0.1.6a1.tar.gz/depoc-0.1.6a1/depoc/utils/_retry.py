import functools

from time import sleep
from requests.exceptions import RequestException


def retry(retries=3, delay=1):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(retries):
                try:
                    return func(*args, **kwargs)
                except (RequestException) as e:
                    if attempt == retries - 1:
                        raise
                    sleep(delay * (2 ** attempt))
            return func(*args, **kwargs)
        return wrapper
    return decorator
