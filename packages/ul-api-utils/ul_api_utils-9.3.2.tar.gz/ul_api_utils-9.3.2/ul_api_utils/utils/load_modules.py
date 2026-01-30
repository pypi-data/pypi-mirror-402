import importlib
import os
from typing import List, Optional, Tuple

from ul_py_tool.utils.arg_files_glob import arg_files_glob, arg_file_glob_compile_files


def load_modules_by_template(include: List[str], exclude: Optional[List[str]] = None) -> Tuple[List[str], List[str]]:
    find = arg_files_glob(ignore_absent=True)
    files, ignored = arg_file_glob_compile_files(include=[find(tpl) for tpl in include], exclude=[find(tpl) for tpl in (exclude or [])])
    for file in files:
        file_rel = os.path.relpath(file, os.getcwd())
        mdl = file_rel[:-len('.py')].replace('\\', '/').strip('/').replace('/', '.')
        importlib.import_module(mdl)
    return files, ignored
