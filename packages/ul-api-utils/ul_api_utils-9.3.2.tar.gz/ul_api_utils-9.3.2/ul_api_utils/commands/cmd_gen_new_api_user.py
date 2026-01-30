import argparse
import logging
import os.path
from requests.exceptions import HTTPError

import requests
from datetime import datetime
from typing import List, Optional, Any, Dict


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


class CmdGenerateNewApiUser(Cmd):
    uri_auth_api: str
    internal_access_key: str
    permissions_list: List[int]
    permissions_uri: Optional[str] = None
    api_user_name: str
    api_user_note: str
    api_user_date_exp: datetime
    dir: str

    @staticmethod
    def add_parser_args(parser: argparse.ArgumentParser) -> None:
        parser.add_argument('--uri', dest='uri_auth_api', type=str, required=True)
        parser.add_argument('--key', dest='internal_access_key', type=str, required=True)
        parser.add_argument('--name', dest='api_user_name', type=str, required=True)
        parser.add_argument('--note', dest='api_user_note', type=str, required=True)
        parser.add_argument('--exp-dt', dest='api_user_date_exp', type=short_date_validator, required=True)
        parser.add_argument('--permissions', dest='permissions_list', nargs='*', required=False, default=[], type=int)
        parser.add_argument('--permissions-uri', dest='permissions_uri', type=str, required=False, default=None)
        parser.add_argument('--result-dir', dest='dir', type=str, required=False, default=os.path.join(os.getcwd(), '.tmp', f'api-user-tokens-{datetime.now().date().isoformat()}'))

    def run(self) -> None:
        write_stdout('')
        os.makedirs(self.dir, exist_ok=True)

        structure: Dict[str, Any] = dict()

        # generate permissions list
        permissions_list: List[int] = self.permissions_list
        if self.permissions_uri and not permissions_list:
            permissions_response = requests.get(self.permissions_uri)
            assert permissions_response.status_code == 200, f'permissions requests faild. {permissions_response.status_code} :: {permissions_response.json()}'
            permissions_json = permissions_response.json()
            assert 'payload' in permissions_json
            permissions_payload: List[Dict[str, str | int]] = permissions_json['payload']

            for permissions_dict in permissions_payload:
                permissions_list.extend([p['id'] for p in permissions_dict.get('permissions')])  # type: ignore

        api_user_payload = {
            'name': self.api_user_name,
            'note': self.api_user_note,
            'permissions': permissions_list,
            'date_expiration': self.api_user_date_exp.isoformat(),
        }
        api_user_headers = {
            'Authorization': f'Bearer {self.internal_access_key}',
        }

        try:
            new_api_user_request = requests.post(
                url=f"{self.uri_auth_api}/api/v1/tokens",
                json=api_user_payload,
                headers=api_user_headers,
            )
            new_api_user_request.raise_for_status()
            new_api_user_data = new_api_user_request.json()['payload']
        except HTTPError as e:
            logger.info(new_api_user_request.json())
            logger.error(f'request for create api user failed :: {new_api_user_request.status_code} status code :: {e}')
            raise
        structure['meta'] = {}
        structure['meta']['uri'] = self.uri_auth_api
        structure['meta']['name'] = self.api_user_name
        structure['meta']['note'] = self.api_user_note
        structure['meta']['permissions'] = permissions_list
        structure['meta']['date_expiration'] = self.api_user_date_exp
        structure[self.api_user_name] = {}
        structure[self.api_user_name]['id'] = new_api_user_data['id']
        structure[self.api_user_name]['token'] = new_api_user_data['access_token']

        result_file_name = f'{self.api_user_name}__{datetime.now().date()}__api_user_data.yml'

        with open(os.path.join(self.dir, result_file_name), 'w') as f:
            dump(structure, f, sort_keys=False)
            write_stdout(f'   {FG_GREEN}saved:{NC} {os.path.relpath(f.name, os.getcwd())}')

        write_stdout('')
        write_stdout(f'{FG_GREEN}DONE{NC}')
