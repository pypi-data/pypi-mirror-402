import click
from .client import Client
from collections.abc import Callable, Sequence
from radkit_client.async_.logging import init_nglog as init_nglog

__all__ = ['init_nglog', 'start_radkit_client', 'run_radkit_client', 'monkey_patch_typing_fix_generic_signature']

def start_radkit_client(*, client: Client, interactive: bool = False, script: str | None, script_args: Sequence[str] | None) -> None: ...
def run_radkit_client(*, client: Client, scope: dict[str, object], interactive: bool = True, interactive_help_func: Callable[[], None] | None = None, script: str | None = None, script_args: Sequence[str] | None = None, domain: str | None = None) -> None: ...
def monkey_patch_typing_fix_generic_signature() -> None: ...
