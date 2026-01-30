import gc
from typing import Any

from ul_py_tool.utils.write_stdout import write_stdout


def when_ready(server: Any) -> None:
    """
    Use only with --preload option.
    Called just after the server is started.
    Freeze garbage collector objects after preloading the application.
    https://docs.gunicorn.org/en/20.1.0/settings.html?highlight=preload#when-ready
    """
    gc.freeze()
    write_stdout("Objects frozen in permanent generation: ", gc.get_freeze_count())


def post_fork(server: Any, worker: Any) -> None:
    """
    Works only with --preload.
    Called just after a worker has been forked.
    Enable garbage collection on each worker if it's not enabled for some reason.
    https://docs.gunicorn.org/en/20.1.0/settings.html?highlight=preload#post-fork
    """
    write_stdout("Enabling GC for worker", worker.pid)
    gc.enable()
