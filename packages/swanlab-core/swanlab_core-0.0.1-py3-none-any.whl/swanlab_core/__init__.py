from .client import SwanLabClient

_client = None

def _get_client():
    global _client
    if _client is None:
        _client = SwanLabClient()
    return _client

def Log(key: str, value: float):
    """
    Log a scalar value.
    """
    client = _get_client()
    client.log(key, value)
