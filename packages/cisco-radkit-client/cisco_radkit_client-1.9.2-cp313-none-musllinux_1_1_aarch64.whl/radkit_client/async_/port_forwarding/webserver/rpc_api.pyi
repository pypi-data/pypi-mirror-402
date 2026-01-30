from ...client import AsyncClient as AsyncClient
from ...device import AsyncDevice as AsyncDevice
from ...service import AsyncService as AsyncService
from _typeshed import Incomplete
from dataclasses import dataclass
from pydantic import BaseModel
from radkit_client.async_.joining import AsyncJoinedTasks as AsyncJoinedTasks
from typing import Any

class PromptDetectionStrategyModel(BaseModel):
    name: str
    options: dict[str, Any] | None

class BaseExecModel(BaseModel):
    service_id: str
    timeout: int
    reset_before: bool
    reset_after: bool
    sudo: bool
    prompt_detection_strategy: PromptDetectionStrategyModel | None

class SimpleExecRequestModel(BaseExecModel):
    command: str
    device_name: str
    model_config: Incomplete

class MatrixExecRequestModel(BaseExecModel):
    commands: list[str]
    device_names: list[str]
    model_config: Incomplete

class MatrixExecResponseChunkModel(BaseModel):
    device_name: str
    command: str
    success: bool
    raw_data: str

@dataclass
class RpcApi:
    client: AsyncClient
    api_router = ...
    def __post_init__(self) -> None: ...
