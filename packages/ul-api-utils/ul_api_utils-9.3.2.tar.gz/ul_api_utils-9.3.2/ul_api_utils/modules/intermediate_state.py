from typing import Optional, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from ul_api_utils.modules.api_sdk import ApiSdk
    from ul_api_utils.modules.worker_sdk import WorkerSdk


_configured_sdk: Optional[str] = None
_initialized_sdk: Optional[str] = None


def try_configure(obj: Union['ApiSdk', 'WorkerSdk']) -> None:
    global _configured_sdk
    if _configured_sdk is not None:
        raise OverflowError(f'configured ApiSdk/WorkerSdk must be only one! {_configured_sdk} has already configured. Please check your isolation of imports.')
    _configured_sdk = type(obj).__name__


def try_init(obj: Union['ApiSdk', 'WorkerSdk'], app_name: str) -> str:
    if _configured_sdk is None:
        raise OverflowError(f'{type(obj).__name__} was not configured')

    assert isinstance(app_name, str) and len(app_name.strip()) > 0, f'app_name must be NOT EMPTY str. "{type(app_name).__name__}" was given'

    global _initialized_sdk
    if _initialized_sdk is not None:
        raise OverflowError(
            'initialized ApiSdk/WorkerSdk must be only one! '
            f'{_configured_sdk} with name="{app_name}" has already initialized. '
            'Please check your isolation of imports.',
        )
    _initialized_sdk = app_name

    return app_name.strip()
