import contextlib
import os
import sys
import tracemalloc
from typing import Dict, Optional, Iterator

import math
from ul_py_tool.utils.colors import FG_BLUE, NC, FG_GRAY, FG_YELLOW, FG_GREEN
from ul_py_tool.utils.write_stdout import write_stdout


def display_stat(name: str, stat: Dict[str, float], sort_by_value: bool = False, color: Optional[str] = None) -> None:
    stat_max_len = max(len(key) for key in stat.keys())
    max_val = max(v for v in stat.values()) if len(stat) > 1 else 1.

    if sort_by_value:
        sorted_keys = sorted(stat.keys(), key=stat.get)  # type: ignore
    else:
        sorted_keys = sorted(stat.keys())

    chart_width = 30
    write_stdout(f'\n{name}:')
    for key in sorted_keys:
        clr = color
        if clr is None:
            clr = FG_BLUE if key.endswith(".py") else FG_GRAY
        value = stat[key]
        chart_size = (math.ceil(value * chart_width / max_val) if max_val else 0)
        write_stdout(f'{key.strip().strip(os.sep).strip(): <{stat_max_len}} = {clr}{value: >10.3f} KiB [{"▉" * chart_size}{" " * (chart_width - chart_size)}]{NC}')


@contextlib.contextmanager
def trace_malloc(show_all: bool = True, show_libs: bool = True, show_code: bool = True) -> Iterator[None]:
    tracemalloc.start()

    yield

    snapshot = tracemalloc.take_snapshot()

    snapshot = snapshot.filter_traces((
        tracemalloc.Filter(False, "<frozen importlib._bootstrap>"),
        tracemalloc.Filter(False, "<frozen importlib._bootstrap_external>"),
        tracemalloc.Filter(False, "<unknown>"),
    ))

    top_stats = snapshot.statistics('filename')

    sites_packages = '/site-packages/'
    cwd = os.path.normpath(os.path.abspath(os.getcwd()))

    libs_stat: Dict[str, float] = {}
    code_stat: Dict[str, float] = {}
    all_files_stat: Dict[str, float] = {}
    other_stat: Dict[str, float] = {}

    for st in top_stats:
        frame = st.traceback[0]
        fname = os.path.normpath(os.path.abspath(frame.filename))
        fname_segm = fname.strip().split(os.sep)
        size = st.size / 1024

        if not fname.endswith('.py'):
            other_stat[fname] = other_stat.get(fname, 0.) + size
            continue

        for i in range(len(fname_segm)):
            key = os.sep.join(fname_segm[:i + 1])
            all_files_stat[key] = all_files_stat.get(key, 0.) + size

            if key.startswith(sys.prefix) and sites_packages in key:
                i = key.index(sites_packages)
                lib_key = "/".join(key[i:].split(os.sep)[2:3])
                if lib_key:
                    libs_stat[lib_key] = libs_stat.get(lib_key, 0.) + size
            elif key.startswith(cwd):
                code_key = key.removeprefix(cwd)
                code_stat[code_key] = code_stat.get(code_key, 0.) + size

    if show_all:
        display_stat('All Files', all_files_stat)

    if show_libs:
        display_stat('Libs', libs_stat, sort_by_value=True, color=FG_YELLOW)

    if show_code:
        display_stat('Code', code_stat, sort_by_value=True, color=FG_BLUE)

    display_stat('Other', other_stat, sort_by_value=True, color=FG_BLUE)

    total = sum(st.size for st in top_stats)
    write_stdout(f"{FG_GREEN}Total allocated size: {(total / 1024):.3f} KiB{NC}")

    tracemalloc.stop()
