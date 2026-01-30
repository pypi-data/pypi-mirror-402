import argparse
import logging
import os.path
from uuid import UUID

from requests.exceptions import HTTPError

import requests
from datetime import datetime
from typing import Any, Dict


from ul_py_tool.commands.cmd import Cmd
from ul_py_tool.utils.colors import FG_GREEN, NC
from ul_py_tool.utils.write_stdout import write_stdout
from yaml import dump


logger = logging.getLogger(__name__)


def short_date_validator(value: str) -> datetime:
    try:
        return datetime.combine(datetime.strptime(value, "%Y-%m-%d"), datetime.max.time())
    except ValueError:
        msg = "not a valid date: {0!r}".format(value)
        raise argparse.ArgumentTypeError(msg)


class CmdGenerateApiUserToken(Cmd):
    uri_auth_api: str
    internal_access_key: str
    api_user_id: UUID
    dir: str

    @staticmethod
    def add_parser_args(parser: argparse.ArgumentParser) -> None:
        parser.add_argument('--uri', dest='uri_auth_api', type=str, required=True)
        parser.add_argument('--key', dest='internal_access_key', type=str, required=True)
        parser.add_argument('--id', dest='api_user_id', type=UUID, required=True)
        parser.add_argument('--result-dir', dest='dir', type=str, required=False, default=os.path.join(os.getcwd(), '.tmp', f'api-user-tokens-{datetime.now().date().isoformat()}'))

    def run(self) -> None:
        write_stdout('')
        os.makedirs(self.dir, exist_ok=True)

        structure: Dict[str, Any] = dict()

        api_user_headers = {
            'Authorization': f'Bearer {self.internal_access_key}',
        }

        try:
            new_api_user_token_request = requests.post(
                url=f"{self.uri_auth_api}/api/v1/tokens/{self.api_user_id}",
                headers=api_user_headers,
            )
            new_api_user_token_request.raise_for_status()
            new_api_user_token = new_api_user_token_request.json()['payload']
        except HTTPError as e:
            logger.info(new_api_user_token_request.text)
            logger.error(f'request for create api user failed :: {new_api_user_token_request.status_code} status code :: {e}')
            raise

        structure['meta'] = {}
        structure['meta']['uri'] = self.uri_auth_api
        structure[str(self.api_user_id)] = {}
        structure[str(self.api_user_id)]['token'] = new_api_user_token['access_token']

        result_file_name = f'{self.api_user_id}__{datetime.now().date()}__api_user_token.yml'

        with open(os.path.join(self.dir, result_file_name), 'w') as f:
            dump(structure, f, sort_keys=False)
            write_stdout(f'   {FG_GREEN}saved:{NC} {os.path.relpath(f.name, os.getcwd())}')

        write_stdout('')
        write_stdout(f'{FG_GREEN}DONE{NC}')
