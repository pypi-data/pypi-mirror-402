import ssl
from ..base import AnySocketStream
from .base import SocketStreamHandler
from _typeshed import Incomplete
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from cryptography import x509
from cryptography.hazmat.primitives.asymmetric import rsa
from dataclasses import dataclass
from radkit_client.async_.settings import AllClientSettings
from typing_extensions import Self

__all__ = ['wrap_in_tls', 'wrap_handler_in_tls', 'ProxyTLSCertificate', 'TlsWrapper', 'TlsHandshakeFailedError']

@asynccontextmanager
async def wrap_in_tls(settings: AllClientSettings, client_sock_stream: AnySocketStream) -> AsyncGenerator[TlsWrapper]: ...
def wrap_handler_in_tls(settings: AllClientSettings, handler: SocketStreamHandler) -> SocketStreamHandler: ...

@dataclass
class ProxyTLSCertificate:
    key: rsa.RSAPrivateKey
    certificate: x509.Certificate
    @classmethod
    def certs_are_already_present(cls, settings: AllClientSettings) -> bool: ...
    @classmethod
    def generate(cls) -> Self: ...
    def write(self, settings: AllClientSettings) -> None: ...

class TlsWrapper:
    ssl_context: Incomplete
    client_sock_stream: Incomplete
    def __init__(self, ssl_context: ssl.SSLContext, client_sock_stream: AnySocketStream) -> None: ...
    @asynccontextmanager
    async def open(self) -> AsyncGenerator[Self]: ...
    def selected_protocol(self) -> str: ...
    async def send(self, data: bytes) -> None: ...
    async def send_eof(self) -> None: ...
    async def receive(self, number: int = 0) -> bytes: ...

class TlsHandshakeFailedError(Exception): ...
