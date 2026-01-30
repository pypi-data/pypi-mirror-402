import json
import time
from enum import Enum
from json import JSONEncoder
from typing import Dict, Any, Union, List, NamedTuple

from ul_api_utils.const import RESPONSE_PROP_DEBUG_STATS, API_PATH__DEBUGGER_JS_UI, API_PATH__DEBUGGER_JS_MAIN
from ul_api_utils.debug import stat
# https://www.w3schools.com/js/js_cookies.asp
from ul_api_utils.debug.stat import collecting_enabled
from ul_api_utils.utils.api_method import ApiMethod
from ul_api_utils.utils.api_path_version import ApiPathVersion
from ul_api_utils.utils.colors import COLORS_MAP__TERMINAL


class DebuggerJSONEncoder(JSONEncoder):
    def default(self, obj: object) -> Union[str, Dict[str, Any], List[Any], None]:
        if isinstance(obj, tuple):
            return list(obj)
        if isinstance(obj, Enum):
            return str(obj.value)
        if isinstance(obj, set):
            return list(obj)
        if hasattr(obj, "__html__"):  # it needs for Flask ?
            return str(obj.__html__())
        return super().default(obj)


AJAX_INTERSEPTOR = """
<script>
(function(window) {
    "use strict";

const {fetch: origFetch} = window;
window.fetch = (resource, options = {}, ...args) => {
  const startedAt = Date.now() / 1000;
  const p = origFetch(resource, options, ...args);

  p
  .then((resp) => {
    return resp.clone().json().then((result) => {
        if (window.addDebuggerRequestStats != null) {
            window.addDebuggerRequestStats(options.method, resource, startedAt, Date.now() / 1000, result._debug_stats_, resp.statusCode)
        }
    })
  })
  .catch((err) => console.error(err))

  return p;
};
})(window);
</script>
"""


class DebuggerError(NamedTuple):
    err: Exception
    tb: str
    at: float


class Debugger:

    __slots__ = (
        'name',
        'enabled',
        'method',
        'url',
    )

    def __init__(self, name: str, enabled: bool, method: ApiMethod, url: str) -> None:
        self.name = name
        self.enabled = enabled
        self.method = method
        self.url = url

    def render_console(self) -> None:
        if not self.enabled:
            return

        started_at = stat.get_request_started_at()
        ended_at = time.perf_counter()
        name = self.name

        stats = stat.get_stat(code_spans=True, started_at=started_at, ended_at=ended_at)
        stat_str = stat.mk_stat_string(name, stats, started_at=started_at, ended_at=ended_at, truncate_request_len=None, trim_txt_new_line=True, cm=COLORS_MAP__TERMINAL)

        print(f'\n{stat_str}\n')  # noqa

    def render_dict(self, status_code: int) -> Dict[str, Any]:
        if not collecting_enabled():
            return {}
        stats = [st.unwrap() for st in stat.get_stat(started_at=stat.get_request_started_at(), ended_at=time.perf_counter())]

        return {
            RESPONSE_PROP_DEBUG_STATS: stats,
        }

    def render_html(self, status_code: int) -> str:
        script = (
            f'<script '
            f'data-ul-debugger="{ApiPathVersion.NO_VERSION.compile_path(API_PATH__DEBUGGER_JS_MAIN, prefix="/api")}" '
            f'src="{ApiPathVersion.NO_VERSION.compile_path(API_PATH__DEBUGGER_JS_UI, prefix="/api")}" '
            f'></script>'
        )
        if not self.enabled:
            return script

        started_at = stat.get_request_started_at()
        ended_at = time.perf_counter()

        stats = stat.get_stat(code_spans=True, started_at=started_at, ended_at=ended_at)

        return (
            f'{script}'
            '<script>setTimeout(function(){{\n'
            f'window.addDebuggerRequestStats("{self.method.value}", "{self.url}", {started_at}, {ended_at}, {json.dumps(stats, cls=DebuggerJSONEncoder)}, {status_code});'
            '\n}}, 300);</script>'
        )
