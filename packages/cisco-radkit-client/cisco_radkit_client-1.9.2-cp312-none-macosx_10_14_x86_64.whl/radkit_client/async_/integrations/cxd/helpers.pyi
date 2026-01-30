from collections.abc import Mapping
from radkit_client.async_.settings import AllClientSettings

__all__ = ['cxd_exceptions', 'cxd_token_url']

cxd_exceptions: Mapping[int, type[Exception]]

def cxd_token_url(settings: AllClientSettings, target: str) -> str: ...
