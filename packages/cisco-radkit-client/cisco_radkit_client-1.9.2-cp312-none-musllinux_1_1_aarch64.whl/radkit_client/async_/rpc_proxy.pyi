from .exceptions import ClientError
from .service import AsyncService
from .state import AsyncServiceState
from _typeshed import Incomplete
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from radkit_common.rpc import E2EEInfo, EndToEndBackend, RPCName, RPCSource, RPCTarget, VerifySessionData, VerifySessionFailed, VerifySessionSuccess, VerifyUserData, VerifyUserFailed, VerifyUserSuccess
from radkit_common.rpc.proxy import RPCProxyApprover
from radkit_common.types import CustomSecretStr

__all__ = ['AsyncServiceRpcProxy']

class AsyncServiceRpcProxy:
    __pt_repr__: Incomplete
    def __init__(self, service_state: AsyncServiceState) -> None: ...
    def target(self) -> RPCTarget: ...
    def status(self) -> RpcProxyStatus: ...
    async def start(self, port: int, username: str, password: CustomSecretStr | str, host: str = 'localhost', approver: RPCProxyApprover | None = None) -> None: ...
    async def start_unix(self, path: Path, username: str, password: CustomSecretStr | str, approver: RPCProxyApprover | None = None) -> None: ...
    async def stop(self) -> None: ...
    def service(self) -> AsyncService: ...

@dataclass
class RpcProxyEndToEndBackend(EndToEndBackend):
    e2ee_info: E2EEInfo
    username: str
    access_token: CustomSecretStr
    def get_e2ee_info(self) -> E2EEInfo: ...
    def require_e2ee(self, rpc_source: RPCSource, rpc_name: RPCName) -> bool: ...
    def require_e2ee_session_verification(self, rpc_source: RPCSource, rpc_name: RPCName) -> bool: ...
    async def verify_session(self, data: VerifySessionData) -> VerifySessionSuccess | VerifySessionFailed: ...
    async def verify_user(self, data: VerifyUserData) -> VerifyUserFailed | VerifyUserSuccess: ...

class RpcProxyStatus(Enum):
    STOPPED = 'STOPPED'
    STOPPING = 'STOPPING'
    RUNNING = 'RUNNING'

@dataclass
class RpcProxyAlreadyStartedError(ClientError):
    listening_on: set[tuple[str, int]]
    listening_on_unix: set[Path]
    username: str
    password: CustomSecretStr
