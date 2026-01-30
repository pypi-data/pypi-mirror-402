from pydantic import ConfigDict, BaseModel

from ul_api_utils.resources.socketio import SocketIOConfig


class WorkerSdkConfig(BaseModel):
    socket_config: SocketIOConfig | None = None

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        arbitrary_types_allowed=True,
    )
