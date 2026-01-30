from enum import Enum
from pathlib import Path
from pydantic import ByteSize, NonNegativeInt, PositiveFloat, PositiveInt
from radkit_client.async_.paths import AsyncClientPaths
from radkit_common import nglog
from radkit_common.domains import Domain
from radkit_common.nglog.config import LoggingFormat
from radkit_common.settings import CommonSettings, EmptyStringOptional, PasswordPolicySettings, SettingsModel, Theme
from radkit_common.settings.base import PathName
from radkit_common.settings.common import BaseLoggingSettings
from radkit_common.settings.validators import validate_file_size_limit
from typing import Annotated

__all__ = ['UseE2EE', 'CXDSettings', 'BDBSettings', 'LoggingSettings', 'ProxyForwarderSettings', 'NetworkConsoleSettings', 'ClientSettings', 'AllClientSettings']

class UseE2EE(str, Enum):
    NEVER = 'NEVER'
    ALWAYS = 'ALWAYS'
    WHEN_AVAILABLE = 'WHEN_AVAILABLE'

class CXDSettings(SettingsModel, env_prefix='RADKIT_CLIENT_CXD_'):
    token_url: str
    auth_url: str
    connection_timeout: PositiveInt

class BDBSettings(SettingsModel, env_prefix='RADKIT_CLIENT_BDB_'):
    api_url: str
    dev_mode: bool
    is_experimental: bool
    allow_external: bool
    timeout: PositiveFloat

class LoggingSettings(BaseLoggingSettings, env_prefix='RADKIT_CLIENT_LOGGING_'):
    file_name: PathName
    directory: EmptyStringOptional[Path]
    level: nglog.LogLevel
    silent: bool
    tracebacks: bool
    format: LoggingFormat
    file_size_limit_bytes: Annotated[ByteSize, validate_file_size_limit]
    backup_count: NonNegativeInt
    session_logging: bool
    session_log_directory: EmptyStringOptional[Path]
    session_log_max_age: PositiveInt
    session_log_file_size_limit_bytes: Annotated[ByteSize, validate_file_size_limit]
    console_limit_replenish: NonNegativeInt
    console_limit_burst: NonNegativeInt
    file_limit_replenish: NonNegativeInt
    file_limit_burst: NonNegativeInt

class ProxyForwarderSettings(SettingsModel, env_prefix='RADKIT_CLIENT_PROXY_FORWARDER_'):
    timeout: PositiveFloat
    h2_max_concurrent_streams: PositiveInt

class NetworkConsoleSettings(SettingsModel, env_prefix='RADKIT_NETWORK_CONSOLE_'):
    profile: EmptyStringOptional[Path]
    enable_history: bool
    history: EmptyStringOptional[Path]
    enable_sr_context: bool
    auto_upload_by_default: bool
    snmp_timeout: NonNegativeInt
    snmp_retries: NonNegativeInt

class ClientSettings(SettingsModel, env_prefix='RADKIT_CLIENT_'):
    pythonstartup: EmptyStringOptional[Path]
    profile: EmptyStringOptional[Path]
    enable_history: bool
    history: EmptyStringOptional[Path]
    default_domain: Annotated[str, None]
    file_chunk_size: PositiveInt
    request_send_timeout: PositiveFloat
    debug_requests: bool
    session_logging: bool
    use_e2ee_default: UseE2EE
    use_h2_when_available: bool
    enable_cloud_request_resubmit: bool
    logging: LoggingSettings
    cxd: CXDSettings
    bdb: BDBSettings
    network_console: NetworkConsoleSettings
    proxy_forwarder: ProxyForwarderSettings
    password_policy: PasswordPolicySettings
    sso_login_open_browser_default: bool
    theme: Annotated[Theme, None]
    def get_default_domain_obj(self) -> Domain: ...

class AllClientSettings(CommonSettings, env_prefix=None):
    client: ClientSettings
    def paths(self) -> AsyncClientPaths: ...
