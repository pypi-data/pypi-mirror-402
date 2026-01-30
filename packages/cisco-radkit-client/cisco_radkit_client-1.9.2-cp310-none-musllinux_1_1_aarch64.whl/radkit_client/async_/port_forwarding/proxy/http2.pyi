from ..base import AnySocketStream
from .base import HttpRequestHandler, WebSocketRequestHandler
from dataclasses import dataclass
from radkit_client.async_.settings.client import AllClientSettings

__all__ = ['Http2Forwarder']

@dataclass
class Http2Forwarder:
    socket_stream: AnySocketStream
    request_handler: HttpRequestHandler
    websocket_request_handler: WebSocketRequestHandler | None
    settings: AllClientSettings
    def __post_init__(self) -> None: ...
    async def run(self) -> None: ...
