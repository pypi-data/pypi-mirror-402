import contextlib
import time
import traceback
import uuid
from datetime import datetime
from enum import Enum, unique
from typing import List, Optional, NamedTuple, Dict, Any, Generator, Tuple

from flask import g

from ul_api_utils.conf import APPLICATION_DEBUGGER_PIN
from ul_api_utils.const import REQUEST_HEADER__DEBUGGER
from ul_api_utils.utils.api_method import ApiMethod
from ul_api_utils.utils.colors import COLORS_MAP__TERMINAL, C_NC, C_FG_GRAY, C_FG_GREEN, C_FG_RED, C_FG_YELLOW

IND = '  '
INDENT = '    '


def time_now() -> float:
    return time.perf_counter()


def mark_request_started() -> None:
    g.debug_api_utils_request_started_at = time_now()  # type: ignore


def get_request_started_at() -> float:
    return getattr(g, 'debug_api_utils_request_started_at', 0.)


def add_request_stat(stat: 'ApiUtilCallStat') -> None:
    try:
        stats = g.debug_api_utils_request_stat  # type: ignore
    except AttributeError:
        stats = g.debug_api_utils_request_stat = []  # type: ignore
    stats.append(stat)


def get_request_stat() -> List['ApiUtilCallStat']:
    return getattr(g, 'debug_api_utils_request_stat', [])


@unique
class ApiUtilCallStatType(Enum):
    HTTP_REQUEST = 'http'
    SQL_QUERY = 'sql'
    CODE = 'code'
    FILE = 'file'

    def __repr__(self) -> str:
        return f'{type(self).__name__}.{self.name}'


STAT_TYPE_COLORS: Dict[ApiUtilCallStatType, str] = {
    ApiUtilCallStatType.HTTP_REQUEST: "",
    ApiUtilCallStatType.SQL_QUERY: "",
    ApiUtilCallStatType.CODE: C_FG_GRAY,
    ApiUtilCallStatType.FILE: "",
}

assert set(STAT_TYPE_COLORS.keys()) == set(ApiUtilCallStatType)


MAX_LEN_OF_TYPE = max(len(v.value) for v in ApiUtilCallStatType)

prog_blocks = (
    ('▉', 0.85),
    ('▊', 0.75),
    ('▋', 0.6),
    ('▌', 0.5),
    ('▍', 0.4),
    ('▎', 0.2),
    ('▏', 0.1),
    ('', 0.0),
)


def term_chart(length: int, normalized_value: float) -> str:
    val = round(normalized_value * length, 1)
    suf = ''
    res = val - float(int(val))
    for b, v in prog_blocks:
        if res >= v:
            suf = b
            break
    return f"{'█' * int(val)}{suf}".ljust(length, '_')


def col_duration(
    started_at: float,
    ended_at: Optional[float],
    *,
    max_len: int = 5,
    max_duration: Optional[float] = None,
    chart_size: int = 10,
    cm: Dict[str, str] = COLORS_MAP__TERMINAL,
) -> str:
    if ended_at is None:
        return str('N/A                 ')[:max_len + 1]
    duration = ended_at - started_at
    dur_fg = cm[C_FG_RED] if duration > 0.3 else (cm[C_FG_YELLOW] if duration > 0.1 else cm[C_NC])
    durations = f'{duration:.10f}'
    chart = f'▕{dur_fg}{term_chart(chart_size, duration / max_duration)}{cm[C_NC]}▏' if max_duration is not None and max_duration > 0. else ''
    return f'{dur_fg}{durations[:max_len]}s{cm[C_NC]}{chart}'


class ApiUtilCallStat(NamedTuple):
    type: ApiUtilCallStatType
    started_at: float
    ended_at: Optional[float]
    text: str
    status: str
    ok: bool
    lvl: int
    http_params: Optional[Tuple[Optional[str], str]] = None

    def unwrap(self) -> Tuple[str, float, Optional[float], str, str, bool, int, Optional[Tuple[Optional[str], str]]]:
        return (
            self.type.value,
            self.started_at,
            self.ended_at,
            self.text,
            self.status,
            self.ok,
            self.lvl,
            self.http_params,
        )

    @staticmethod
    def wrap(add_lvl: int, *args: Any) -> Optional['ApiUtilCallStat']:
        if len(args) not in {7, 8}:
            return None
        try:
            return ApiUtilCallStat(
                type=ApiUtilCallStatType(args[0]),
                started_at=args[1],
                ended_at=args[2],
                text=args[3],
                status=args[4],
                ok=args[5],
                lvl=args[6] + add_lvl,
                http_params=args[7] if len(args) == 8 else None,
            )
        except Exception:  # noqa: B902
            return None

    @property
    def duration_s(self) -> Optional[float]:
        return self.ended_at - self.started_at if self.ended_at is not None else None


def collecting_enabled() -> bool:
    return getattr(g, 'debug_api_utils_collect_stat', False)


def collecting_enable(enabled: bool) -> None:
    g.debug_api_utils_collect_stat = enabled  # type: ignore


def get_stats_request_headers() -> Dict[str, str]:
    if not collecting_enabled():
        return {}
    return {
        REQUEST_HEADER__DEBUGGER: APPLICATION_DEBUGGER_PIN,
    }


def add_http_request_stat(
    *,
    started_at: float,
    method: ApiMethod,
    url: str,
    status_code: Optional[int],
    internal_stats: List[List[Any]],
    request: Optional[str],
    response: str,
) -> None:
    now = time_now()
    add_request_stat(ApiUtilCallStat(
        text=f'{method.value.ljust(6)} {url}',
        status=f'{status_code or "UNKNOWN"}',
        started_at=started_at,
        ended_at=now,
        ok=(status_code is not None) and status_code < 400,
        type=ApiUtilCallStatType.HTTP_REQUEST,
        lvl=0,
        http_params=(request, response),
    ))

    if not isinstance(internal_stats, (list, tuple)):
        return  # type: ignore

    for s in internal_stats:
        st = ApiUtilCallStat.wrap(1, *s)
        if st is None:
            continue
        add_request_stat(st)


def get_stat(*, started_at: float, ended_at: float, code_spans: bool = True, span_threshold: float = 0.01) -> List[ApiUtilCallStat]:
    if not collecting_enabled():
        return []

    stats: List[ApiUtilCallStat] = list(get_request_stat())

    from flask_sqlalchemy.record_queries import get_recorded_queries

    for q in get_recorded_queries():
        ok = q.end_time is not None

        try:
            text = str(q.statement % q.parameters) if len(q.parameters) else q.statement
        except Exception:  # noqa: B902
            text = q.statement
            pass

        stats.append(ApiUtilCallStat(
            type=ApiUtilCallStatType.SQL_QUERY,
            text=text,
            ok=ok,
            started_at=q.start_time,
            ended_at=q.end_time,
            lvl=0,
            status='OK' if ok else 'ERROR',
        ))

    stats = sorted(stats, key=lambda obj: obj.started_at)

    if code_spans:
        if not len(stats):
            code_span = ApiUtilCallStat(
                text='',
                status='OK',
                started_at=started_at,
                ended_at=ended_at,
                ok=True,
                type=ApiUtilCallStatType.CODE,
                lvl=0,
            )
            stats.append(code_span)
        else:
            prev_s: Optional[ApiUtilCallStat] = None
            stats_with_spans = []
            max_dur = 0.
            for s in stats:
                if s.duration_s is not None:
                    max_dur = max(max_dur, s.duration_s)
            first_code_span = ApiUtilCallStat(
                text='',
                status='OK',
                started_at=started_at,
                ended_at=stats[0].started_at,
                ok=True,
                type=ApiUtilCallStatType.CODE,
                lvl=0,
            )
            last_code_span = ApiUtilCallStat(
                text='',
                status='OK',
                started_at=stats[-1].ended_at or 0.,
                ended_at=ended_at,
                ok=True,
                type=ApiUtilCallStatType.CODE,
                lvl=0,
            )
            stats_with_spans.append(first_code_span)
            for s in stats:
                if prev_s is not None:
                    p_ended_at = prev_s.ended_at or 0.
                    span = s.started_at - p_ended_at
                    if round(span, 3) >= span_threshold:
                        stats_with_spans.append(ApiUtilCallStat(
                            text='',
                            status='OK',
                            started_at=p_ended_at,
                            ended_at=s.started_at,
                            ok=True,
                            type=ApiUtilCallStatType.CODE,
                            lvl=prev_s.lvl,
                        ))
                stats_with_spans.append(s)
                prev_s = s
            stats_with_spans.append(last_code_span)
            stats = stats_with_spans

    return stats


class StatMeasure:

    __slots__ = (
        '_title',
        '_started_at',
        '_ok',
        '_errors',
        '_ended_at',
    )

    def __init__(self, title: str) -> None:
        self._title = title
        self._started_at = time_now()
        self._ok = False
        self._errors: List[str] = []
        self._ended_at: Optional[float] = None

    def _internal_use_end(self) -> None:
        assert self._ended_at is None
        self._ended_at = time_now()

    def format(self) -> str:
        txt = self._title.strip()
        if txt:
            txt += '\n'
        for err_string in self._errors:
            txt += f'{err_string.strip()}\n'
        return txt

    @property
    def started_at(self) -> float:
        return self._started_at

    @property
    def ended_at(self) -> Optional[float]:
        return self._ended_at

    def add_error(self, err_string: str = '') -> None:
        assert isinstance(err_string, str), f'err_string must be str. "{type(err_string).__name__}" was given'
        self._ok = False
        assert self._ended_at is None
        self._errors.append(err_string)

    @property
    def ok(self) -> bool:
        return self._ok and len(self._errors) == 0

    @ok.setter
    def ok(self, value: bool) -> None:
        assert self._ended_at is None
        assert isinstance(value, bool), f'value must be bool. "{type(value).__name__}" was given'
        self._ok = value


@contextlib.contextmanager
def measure(title: str, type: ApiUtilCallStatType = ApiUtilCallStatType.CODE) -> Generator[StatMeasure, None, None]:
    mes = StatMeasure(title)
    try:
        yield mes
        mes.ok = True
        mes._internal_use_end()
    except Exception:  # noqa: B902
        mes.add_error(traceback.format_exc())
        mes.ok = False
        mes._internal_use_end()
        raise
    finally:
        add_request_stat(ApiUtilCallStat(
            text=mes.format(),
            status='OK' if mes.ok else 'ERROR',
            started_at=mes.started_at,
            ended_at=mes.ended_at,
            ok=mes.ok,
            type=type,
            lvl=0,
        ))


def mk_stat_string(
    name: str,
    stats: List[ApiUtilCallStat],
    started_at: float,
    ended_at: float,
    truncate_request_len: Optional[int] = None,
    trim_txt_new_line: bool = False,
    cm: Dict[str, str] = COLORS_MAP__TERMINAL,
) -> str:
    max_lvl, max_duration = 0, 0.
    max_len_of_status = 0
    unknown_span = ended_at - started_at
    duration_by_categories = {t.value: 0. for t in ApiUtilCallStatType}
    max_duration_by_category = 0.
    for s in stats:
        if s.duration_s is not None:
            duration_by_categories[s.type.value] += s.duration_s
        max_duration_by_category = max(max_duration_by_category, duration_by_categories[s.type.value])
        if s.lvl == 0 and s.duration_s is not None:
            unknown_span -= s.duration_s
        max_lvl = max(max_lvl, s.lvl)
        max_duration = max(max_duration, s.duration_s or 0.)
        max_len_of_status = max(max_len_of_status, len(str(s.status)))

    total_str = ''
    for cat_type, cat_dur in sorted(duration_by_categories.items(), key=lambda v: v[0]):
        if cat_type == ApiUtilCallStatType.HTTP_REQUEST.value:
            cat_type = f'{cm[C_FG_GRAY]}{cat_type}?{cm[C_NC]}'
        total_str += f'{cat_type}={col_duration(0., cat_dur, max_duration=max_duration_by_category, chart_size=5, cm=cm)}{INDENT}'

    if unknown_span > 0.001:
        total_str += f'unknown={col_duration(0, unknown_span, max_duration=max_duration_by_category, chart_size=5, cm=cm)}'

    result_s = ''
    tree_str_size = 3
    i_size = len(str(len(stats)))
    for i, s in enumerate(stats):
        next_s: Optional[ApiUtilCallStat] = None
        has_next_s_with_same_lvl = False
        if len(stats) >= (i + 2):
            if next_s is None:
                next_s = stats[i + 1]
            for ns in stats[i + 1:]:
                if ns.lvl == s.lvl:
                    has_next_s_with_same_lvl = True
                    break
                if ns.lvl < s.lvl:
                    break
        lvl_pref = ('┃' + ' ' * (len(INDENT) - 1)) * s.lvl if next_s is not None else INDENT * s.lvl
        lvl_suf = INDENT * (max_lvl - s.lvl)
        ok_fg = cm[C_FG_RED] if not s.ok else cm[C_FG_GREEN]
        duration_str = col_duration(s.started_at, s.ended_at, max_duration=max_duration, cm=cm)

        tree_str = '┗'
        if next_s is not None and s.lvl == next_s.lvl:
            tree_str = '┣'
        elif has_next_s_with_same_lvl:
            tree_str = '┣'

        txt = s.text[:truncate_request_len] if truncate_request_len is not None else s.text
        if trim_txt_new_line:
            txt = txt.replace('\n', ' ').replace('\r', ' ')
        result_s += (
            f'{IND}{cm[C_FG_GRAY]}#{i + 1:0>{i_size}}/{len(stats):0>{i_size}}{IND}{lvl_pref}{tree_str:━<{tree_str_size}}{cm[C_NC]}'
            f' {cm[STAT_TYPE_COLORS[s.type]]}{s.type.value: <{MAX_LEN_OF_TYPE}}{cm[C_NC]} '
            f'{IND}{lvl_suf}{duration_str}'
            f'{IND}{ok_fg}{s.status: <{max_len_of_status}}{cm[C_NC]}'
            f'{IND}{cm[C_FG_GRAY]}::{cm[C_NC]}'
            f'{IND}{txt}\n'
        )

    header = f'{IND}{" " * (i_size * 2 + 2)}{IND}Request{" " * MAX_LEN_OF_TYPE}{INDENT * max_lvl}{col_duration(started_at, ended_at, cm=cm)}{INDENT}{INDENT}{total_str}'

    short_identifier = uuid.uuid4().hex[:8]
    return f'▀▀▀▀▀ {name} {cm[C_FG_GRAY]}{short_identifier}{cm[C_NC]}{IND}{"▀" * 55}' \
           f'\n{header}\n' \
           f'{result_s}▄▄▄▄▄ {name} {cm[C_FG_GRAY]}{short_identifier}{cm[C_NC]} {"▄" * 96}'
