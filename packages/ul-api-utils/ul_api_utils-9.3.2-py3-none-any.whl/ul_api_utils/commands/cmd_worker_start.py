import argparse
import os
import re
import subprocess
import sys
from datetime import datetime

from ul_py_tool.commands.cmd import Cmd
from ul_py_tool.utils.arg_str2bool import arg_str2bool

from ul_api_utils.const import APPLICATION_ENV__LOCAL, PY_FILE_SUF


class CmdWorkerStart(Cmd):
    app_dir: str
    env: str
    debug: bool
    worker_name: str
    app_file_name: str = 'main.py'

    @property
    def app_file_path(self) -> str:
        return os.path.join(self.app_dir, self.app_file_name)

    @property
    def app_module(self) -> str:
        file_rel_path = os.path.relpath(self.app_file_path, os.getcwd())
        if file_rel_path.endswith(PY_FILE_SUF):
            file_rel_path = file_rel_path[:-len(PY_FILE_SUF)]
        return re.sub(r'/+', '.', file_rel_path.replace('\\', '/')).strip('.')

    @staticmethod
    def add_parser_args(parser: argparse.ArgumentParser) -> None:
        parser.add_argument('--app-dir', dest='app_dir', type=str, required=True, help="dir to import main.py")
        parser.add_argument('--env', dest='env', type=str, required=True)
        parser.add_argument('--worker', dest='worker_name', type=str, required=True)
        parser.add_argument('--debug', dest='debug', type=arg_str2bool, default=False, required=False)

    def run(self) -> None:
        env = os.environ.copy()
        env['PYTHONUNBUFFERED'] = '1'
        env['PYTHONPATH'] = os.getcwd()
        env['APPLICATION_START_DT'] = datetime.now().isoformat()
        env['APPLICATION_ENV'] = self.env
        env['APPLICATION_DIR'] = self.app_dir
        env['APPLICATION_DEBUG'] = '1' if self.debug else '0'

        if self.debug and self.env == APPLICATION_ENV__LOCAL:
            subprocess.run(
                [
                    'watchmedo',
                    'auto-restart',
                    '--pattern=*.py',
                    '--recursive',
                    f'--directory={os.getcwd()}',
                    f'--command=\'python3 -m {self.app_module} --worker={self.worker_name}\'',
                    '.',
                ],
                cwd=os.getcwd(),
                stdout=sys.stdout,
                stderr=sys.stderr,
                text=True,
                env=env,
            )
        else:
            subprocess.run(
                [
                    'python3', '-m', f'{self.app_module}',
                    f'--worker={self.worker_name}',
                ],
                cwd=os.getcwd(),
                stdout=sys.stdout,
                stderr=sys.stderr,
                text=True,
                env=env,
            )
