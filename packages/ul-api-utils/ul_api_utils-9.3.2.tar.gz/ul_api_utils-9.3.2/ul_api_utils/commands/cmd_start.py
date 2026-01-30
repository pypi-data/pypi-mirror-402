import argparse
import gc
import os
import re
import subprocess
import sys
from datetime import datetime
from typing import Optional

from ul_py_tool.commands.cmd import Cmd
from ul_py_tool.utils.arg_str2bool import arg_str2bool
from ul_py_tool.utils.write_stdout import write_stdout

from ul_api_utils.conf import APPLICATION_GUNICORN_WORKERS
from ul_api_utils.const import THIS_LIB_CWD

ENV_LOCAL = 'local'
PY_FILE_SUF = '.py'


class CmdStart(Cmd):
    app_dir: str
    app_file_name: str = 'main.py'
    app_name: str = 'flask_app'
    env: str
    port: int
    debug: bool
    max_requests: int
    max_requests_jitter: int
    worker_class: str
    freeze_gc: bool
    statsd_endpoint: Optional[str] = None
    statsd_prefix: Optional[str] = None

    @property
    def app_rel_dir(self) -> str:
        return os.path.relpath(self.app_dir, os.getcwd())

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
        parser.add_argument('--app-dir', dest='app_dir', type=str, required=True, help="dir to import ")
        parser.add_argument('--env', dest='env', type=str, required=True)
        parser.add_argument('--port', dest='port', type=int, required=False, default=30000)
        parser.add_argument('--debug', dest='debug', type=arg_str2bool, default=False, required=False)
        parser.add_argument('--max-requests', dest='max_requests', type=int, default=1000, required=False)
        parser.add_argument('--max-requests-jitter', dest='max_requests_jitter', type=int, default=50, required=False)
        parser.add_argument('--worker-class', dest='worker_class', type=str, default='sync', required=False)
        parser.add_argument('--statsd_endpoint', dest='statsd_endpoint', type=str, default=None, required=False)
        parser.add_argument('--statsd_prefix', dest='statsd_prefix', type=str, default=None, required=False)
        parser.add_argument('--freeze-gc', dest='freeze_gc', type=bool, default=False, required=False)

    def run(self) -> None:
        if self.freeze_gc:
            gc.disable()

        env = os.environ.copy()
        name = re.sub(r'[^0-9a-z]+', '-', f'gncrn-{os.path.relpath(self.app_dir, os.getcwd()).lower().strip("/").strip()}')
        env['PYTHONUNBUFFERED'] = os.environ.get('PYTHONUNBUFFERED', '0')
        env['PYTHONPATH'] = os.getcwd()
        env['APPLICATION_START_DT'] = datetime.now().isoformat()
        env['APPLICATION_ENV'] = self.env
        env['APPLICATION_DIR'] = self.app_dir
        env['APPLICATION_DEBUG'] = '1' if self.debug else '0'
        env['FLASK_APP'] = self.app_file_path

        assert len(APPLICATION_GUNICORN_WORKERS) > 0

        debug = (self.debug and self.env == ENV_LOCAL)
        local_conf = os.path.abspath(os.path.normpath(os.path.join(THIS_LIB_CWD, "commands", "start", "gunicorn.conf.local.py")))
        prod_conf = os.path.abspath(os.path.normpath(os.path.join(THIS_LIB_CWD, "commands", "start", "gunicorn.conf.py")))
        gunicorn_config = prod_conf if self.freeze_gc and not debug else local_conf

        args = [
            f'-n={name}',
            f'-w={APPLICATION_GUNICORN_WORKERS}',
            f'--worker-class={self.worker_class}',
            f'-b=0.0.0.0:{self.port}',
            f'--config={gunicorn_config}',
            '--log-level=INFO',
            f'--max-requests={self.max_requests}',
            f'--max-requests-jitter={self.max_requests_jitter}',
            '--timeout=60',
            '--access-logfile=-',
            '--error-logfile=-',
            '--disable-redirect-access-to-syslog',
            *(['--reload'] if debug else ['--preload']),
            f'{self.app_module}:{self.app_name}',
        ]

        if self.statsd_endpoint and self.env != ENV_LOCAL:
            if self.statsd_prefix:
                args.extend([f'--statsd-host={self.statsd_endpoint}', f"--statsd-prefix={self.statsd_prefix}"])
            else:
                args.extend([f'--statsd-host={self.statsd_endpoint}', f"--statsd-prefix={self.app_module.split('.')[1]}_{self.env}"])

        write_stdout(f'name={name}')
        write_stdout(f'args={args}')
        subprocess.run(['gunicorn', '--check-config', '--print-config', *args], cwd=os.getcwd(), stdout=sys.stdout, stderr=sys.stderr, text=True, env=env)
        os.execvpe('gunicorn', args, env)
