import argparse
import ast
import csv
import importlib
import inspect
import os
import logging
from datetime import datetime
from typing import Dict, Callable, Any, List, TextIO
from flask import url_for, Flask
from ul_py_tool.commands.cmd import Cmd

from ul_api_utils import conf

logger = logging.getLogger(__name__)


class CmdGenApiFunctionDocumentation(Cmd):
    api_dir: str
    db_dir: str
    include_api_utils_doc: bool
    include_db_utils_doc: bool
    app_host: str

    @staticmethod
    def add_parser_args(parser: argparse.ArgumentParser) -> None:
        parser.add_argument('--api-dir', dest='api_dir', type=str, required=True)
        parser.add_argument('--db-dir', dest='db_dir', type=str, required=True)
        parser.add_argument('--app-host', dest='app_host', type=str, required=False, default="{baseUrl}")
        parser.add_argument('--include-utils-api', dest='include_api_utils_doc', type=bool, required=False, default=False)
        parser.add_argument('--include-utils-db', dest='include_db_utils_doc', type=bool, required=False, default=False)

    @property
    def api_module(self) -> str:
        return self.api_dir.replace('/', '.')

    @property
    def api_main_module(self) -> str:
        return self.api_dir.replace('/', '.') + ".main"

    def run(self) -> None:
        root_folder = os.getcwd()
        conf.APPLICATION_DIR = os.path.join(root_folder, self.api_dir)  # because sdk uses this variable to load routes
        current_app = self.load_flask_app(self.api_main_module)
        api_utils_functions = self.load_functions(f'{self.api_dir}/utils')
        conf.APPLICATION_DIR = os.path.join(root_folder, self.db_dir)
        db_helper_functions = self.load_functions(f'{self.db_dir}/models_manager')
        db_utils_functions = self.load_functions(f"{self.db_dir}/utils")
        with current_app.app_context():
            current_app.config['SERVER_NAME'] = self.app_host
        csv_data: List[Dict[str, str]] = []
        with current_app.app_context():
            now = datetime.now().isoformat()
            filename = f'.tmp/{now}-doc.md'
            with open(filename, 'w') as file:
                for api_route_id, flask_api_rule in enumerate(current_app.url_map.iter_rules()):
                    options = {}
                    for arg in flask_api_rule.arguments:
                        options[arg] = "[{0}]".format(arg)
                    api_route_methods = ','.join([method for method in flask_api_rule.methods if method not in ('HEAD', 'OPTIONS')])  # type: ignore
                    api_route_path = url_for(flask_api_rule.endpoint, **options).replace('%5B', '[').replace('%5D', ']')
                    func_object = current_app.view_functions[flask_api_rule.endpoint]
                    if not func_object.__module__.startswith(self.api_module):
                        continue
                    csv_data.append({
                        "api_path": api_route_path,
                        "api_methods": api_route_methods,
                        "api_function_name": func_object.__name__,
                    })
                    self.generate_documentation(
                        func_object,
                        file,
                        api_route_id=api_route_id,
                        api_route_path=api_route_path,
                        api_route_methods=api_route_methods,
                        loaded_db_helper_functions=db_helper_functions,
                        loaded_api_utils_functions=api_utils_functions,
                        loaded_db_utils_functions=db_utils_functions,
                    )
        with open(f'.tmp/{now}-doc.csv', 'w') as csvfile:
            fields = ['api_path', 'api_methods', 'api_function_name']
            writer = csv.DictWriter(csvfile, fieldnames=fields)
            writer.writeheader()
            writer.writerows(csv_data)

    @staticmethod
    def load_functions(directory: str) -> Dict[str, Callable[..., Any]]:
        function_name_object__map: dict[str, Callable[..., Any]] = {}
        for root, _dirs, files in os.walk(directory):
            for file in files:
                py_postfix = '.py'
                if file.endswith(py_postfix):
                    module_name = file[:-len(py_postfix)]
                    module_path = os.path.join(root, file)
                    spec = importlib.util.spec_from_file_location(module_name, module_path)
                    assert spec is not None  # only for mypy
                    assert spec.loader is not None  # only for mypy
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    functions = inspect.getmembers(module, inspect.isfunction)
                    for name, func in functions:
                        function_name_object__map[name] = func
        return function_name_object__map

    @staticmethod
    def load_flask_app(api_sdk_module: str) -> Flask:
        module = importlib.import_module(api_sdk_module)
        return module.flask_app

    @staticmethod
    def find_called_functions_in_api(api_function_object: Callable[..., Any]) -> List[Any]:
        calls = []
        source = inspect.getsource(api_function_object)
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    calls.append(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    calls.append(node.func.attr)
                else:
                    continue
        return calls

    def generate_documentation(
        self,
        func_object: Callable[..., Any],
        file_object: TextIO,
        *,
        api_route_id: int,
        api_route_path: str,
        api_route_methods: str,
        loaded_db_helper_functions: Dict[str, Callable[..., Any]],
        loaded_db_utils_functions: Dict[str, Callable[..., Any]],
        loaded_api_utils_functions: Dict[str, Callable[..., Any]],
    ) -> None:
        func_name = func_object.__name__
        functions_called_in_api_route = self.find_called_functions_in_api(func_object)
        docstring = inspect.getdoc(func_object)
        api_docstring = 'None' if docstring is None else docstring

        file_object.write(f"## {api_route_id} Путь апи {api_route_path}\n\n")
        file_object.write(f"####  Имя функции апи: {func_name}\n")
        file_object.write(f"### Апи методы: {api_route_methods}\n\n")
        file_object.write("**Описание апи метода:** \n\n")
        file_object.write(f"```python\n{api_docstring}\n```\n")
        helper_call = 1
        for function_called_in_api_route in functions_called_in_api_route:
            if function_called_in_api_route not in ('transaction_commit', 'and_', 'or_', 'foreign', 'query_soft_delete', 'ensure_db_object_exists', 'db_search'):
                if function_called_in_api_route in loaded_db_helper_functions:
                    helper_func_obj = loaded_db_helper_functions[function_called_in_api_route]
                    helper_docstring = inspect.getdoc(helper_func_obj)
                    helper_docstring = 'None' if helper_docstring is None else helper_docstring

                    file_object.write(f"### {api_route_id}.{helper_call} Вызвана функция работы с БД : {function_called_in_api_route}\n")
                    file_object.write(f"**Описание функции {function_called_in_api_route}:**\n\n")
                    file_object.write(f"```python\n{helper_docstring}\n```\n")
                    helper_call += 1
                elif function_called_in_api_route in loaded_api_utils_functions:
                    if self.include_api_utils_doc:
                        util_func_obj = loaded_api_utils_functions[function_called_in_api_route]
                        util_docstring = inspect.getdoc(util_func_obj)
                        util_docstring = 'None' if util_docstring is None else util_docstring
                        if 'db_tables_used' in util_docstring or 'db_table_used' in util_docstring:
                            file_object.write(f"### {api_route_id}.{helper_call} Вызвана функция работы с БД : {function_called_in_api_route}\n")
                            file_object.write(f"**Описание функции {function_called_in_api_route}:**\n\n")
                            file_object.write(f"```python\n{util_docstring}\n```\n")
                            helper_call += 1
                elif function_called_in_api_route in loaded_db_utils_functions:
                    if self.include_db_utils_doc:
                        util_func_obj = loaded_db_utils_functions[function_called_in_api_route]
                        db_util_docstring = inspect.getdoc(util_func_obj)
                        db_util_docstring = 'None' if db_util_docstring is None else db_util_docstring
                        if 'db_tables_used' in db_util_docstring or 'db_table_used' in db_util_docstring:
                            file_object.write(f"### {api_route_id}.{helper_call} Вызвана функция работы с БД : {function_called_in_api_route}\n")
                            file_object.write(f"**Описание функции {function_called_in_api_route}:**\n\n")
                            file_object.write(f"```python\n{db_util_docstring}\n```\n")
                            helper_call += 1
        file_object.write('-' * 20)
        file_object.write('\n\n')
        file_object.write('\n\n')
