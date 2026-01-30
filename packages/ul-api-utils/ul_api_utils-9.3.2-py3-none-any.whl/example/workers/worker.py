from ul_unipipeline.message.uni_message import UniMessage
from ul_unipipeline.worker.uni_worker import UniWorker
from ul_unipipeline.worker.uni_worker_consumer_message import UniWorkerConsumerMessage

from ul_api_utils.modules.worker_context import WorkerContext
from ul_api_utils.modules.worker_sdk import WorkerSdk
from ul_api_utils.modules.worker_sdk_config import WorkerSdkConfig
from ul_api_utils.resources.socketio import SocketIOConfig, SocketIOConfigType

initialized_worker = WorkerSdk(WorkerSdkConfig(
    socket_config=SocketIOConfig(
        app_type=SocketIOConfigType.EXTERNAL_PROCESS,
        message_queue='redis://localhost:16379',
        logs_enabled=True,
        engineio_logs_enabled=False,
    ),
))


class Msg(UniMessage):
    pass


class HttpNbfiParserWorker(UniWorker[Msg, None]):

    @initialized_worker.handle_message()  # type: ignore
    def handle_message(self, ctx: WorkerContext, message: UniWorkerConsumerMessage[Msg]) -> None:
        pass
