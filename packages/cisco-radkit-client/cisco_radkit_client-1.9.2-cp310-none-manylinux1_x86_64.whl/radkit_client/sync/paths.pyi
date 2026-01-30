from .from_async import SyncWrapper
from _typeshed import Incomplete
from radkit_client.async_.paths import AsyncClientPaths

__all__ = ['ClientPaths']

class ClientPaths(SyncWrapper[AsyncClientPaths]):
    radkit_directory: Incomplete
    proxy_tls_cert_file: Incomplete
    proxy_tls_key_path: Incomplete
    settings_file: Incomplete
    client_history_file: Incomplete
    client_initialization_profile: Incomplete
    client_pythonstartup: Incomplete
    client_logs_directory: Incomplete
    client_session_logs_directory: Incomplete
    console_history_file: Incomplete
    console_initialization_profile: Incomplete
