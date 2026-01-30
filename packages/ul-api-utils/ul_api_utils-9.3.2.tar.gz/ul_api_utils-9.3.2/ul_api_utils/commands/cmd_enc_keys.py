import argparse
import base64
import importlib
import os.path
import sys

import requests
from datetime import datetime
from typing import List, Optional, Any, Dict
from uuid import UUID
import getpass
import socket
# import json

from ul_py_tool.commands.cmd import Cmd
from ul_py_tool.utils.colors import FG_GREEN, NC
from ul_py_tool.utils.write_stdout import write_stdout
from yaml import dump

from ul_api_utils.access import PermissionRegistry
from ul_api_utils.modules.api_sdk_jwt import ApiSdkJwt, ALGORITHMS
# from ul_api_utils.utils.json_encoder import CustomJSONEncoder


class CmdEncKeys(Cmd):
    algo: str
    name: str
    services: List[str]
    dir: str
    permissions_module: Optional[str] = None
    permissions_uri: Optional[str] = None
    env: Optional[str] = None
    org_id: Optional[UUID] = None
    user_id: Optional[UUID] = None

    @staticmethod
    def add_parser_args(parser: argparse.ArgumentParser) -> None:
        parser.add_argument('--algorithm', dest='algo', type=str, choices=ALGORITHMS, required=True)
        parser.add_argument('--service-name', dest='name', type=str, required=True)
        parser.add_argument('--follower-services', dest='services', nargs='*', required=False, default=[], type=str)
        parser.add_argument('--result-dir', dest='dir', type=str, required=False, default=os.path.join(os.getcwd(), '.tmp', f'enc-keys-{datetime.now().date().isoformat()}'))
        parser.add_argument('--jwt-permissions-module', dest='permissions_module', type=str, required=False, default=None)
        parser.add_argument('--jwt-permissions-uri', dest='permissions_uri', type=str, required=False, default=None)
        parser.add_argument('--jwt-environment', dest='env', type=str, required=False, default=None)
        parser.add_argument('--jwt-user-id', dest='user_id', type=UUID, required=False, default=None)
        parser.add_argument('--jwt-organization-id', dest='org_id', type=UUID, required=False, default=None)

    def run(self) -> None:
        write_stdout('')
        os.makedirs(self.dir, exist_ok=True)

        services = set(self.services)

        private_key, pub_key_factory = ApiSdkJwt.generate_cert(self.algo)  # type: ignore
        service_pub_key = pub_key_factory()

        structure: Dict[str, Any] = dict()

        structure['info'] = dict()
        structure['info']['generated_at'] = datetime.now().isoformat()
        structure['info']['generated_user'] = getpass.getuser()
        structure['info']['generated_hostname'] = socket.gethostname()
        structure['info']['generated_algorithm'] = self.algo
        if self.env:
            structure['info']['environment'] = self.env

        structure['service'] = dict()
        structure['service'][self.name] = dict()
        structure['service'][self.name]['public_key'] = base64.b64encode(service_pub_key.encode('utf-8')).decode('utf-8')
        structure['service'][self.name]['private_key'] = base64.b64encode(private_key.encode('utf-8')).decode('utf-8')

        structure['follower_services'] = dict()
        for service in services:
            pub_key = pub_key_factory().encode('utf-8')
            structure['follower_services'][service] = dict()
            structure['follower_services'][service]['public_key'] = base64.b64encode(pub_key).decode('utf-8')
            # structure['follower_services'][service]['private_key'] = ""

        if self.permissions_uri:
            assert self.permissions_uri
            assert self.algo
            assert self.env
            assert self.user_id
            permissions_response = requests.get(self.permissions_uri)
            assert permissions_response.status_code == 200, f'permissions requests faild. {permissions_response.status_code} :: {permissions_response.json()}'
            permissions_json = permissions_response.json()
            assert 'payload' in permissions_json
            permissions_payload: List[Dict[str, str | int]] = permissions_json['payload']

            permissions_list: List[int] = []
            for permissions_dict in permissions_payload:
                permissions_list.extend([p['id'] for p in permissions_dict.get('permissions')])     # type: ignore

            jwt_data = dict(
                environment=self.env,
                user_id=self.user_id,
                organization_id=self.org_id,
                permissions=permissions_list,
                access_expiration_date=datetime(2030, 1, 1),
                refresh_expiration_date=datetime(2030, 1, 1),
            )
            att, _ = ApiSdkJwt.create_jwt_pair(**jwt_data)  # type: ignore
            structure['service'][self.name]['full_access_jwt_token'] = att.encode(private_key, self.algo)  # type: ignore
            # structure['service'][self.name]['full_access_jwt_data'] = json.loads(json.dumps(jwt_data, cls=CustomJSONEncoder))

            for service in self.services:
                if len(service.split(':')) > 1:
                    service_name, service_user_id = service.split(':')
                    try:
                        UUID(service_user_id)
                    except ValueError:
                        raise ValueError(f"invlid user_id type must be UUID hex for follower service - {service_name}")
                    jwt_data['user_id'] = service_user_id
                att, _rtt = ApiSdkJwt.create_jwt_pair(**jwt_data)  # type: ignore
                structure['follower_services'][service]['full_access_jwt_token'] = att.encode(private_key, self.algo)  # type: ignore
                # structure['service'][service]['full_access_jwt_data'] = json.loads(json.dumps(jwt_data, cls=CustomJSONEncoder))

        elif self.permissions_module:
            assert self.permissions_module
            assert self.algo
            assert self.env
            assert self.user_id
            sys.path.append(os.getcwd())
            mdl = importlib.import_module(self.permissions_module)
            permissions = None
            for k in dir(mdl):
                v = getattr(mdl, k)
                if isinstance(v, PermissionRegistry):
                    permissions = v
                    break
            assert permissions is not None

            jwt_data = dict(
                environment=self.env,
                user_id=self.user_id,
                organization_id=self.org_id,
                permissions=permissions.get_permissions_ids(),
                access_expiration_date=datetime(2030, 1, 1),
                refresh_expiration_date=datetime(2030, 1, 1),
            )

            att, _ = ApiSdkJwt.create_jwt_pair(**jwt_data)  # type: ignore
            structure['service'][self.name]['full_access_jwt_token'] = att.encode(private_key, self.algo)  # type: ignore
            # structure['service'][self.name]['full_access_jwt_data'] = json.loads(json.dumps(jwt_data, cls=CustomJSONEncoder))

            for service in self.services:
                if len(service.split(':')) > 1:
                    service_name, service_user_id = service.split(':')
                    try:
                        UUID(service_user_id)
                    except ValueError:
                        raise ValueError(f"invlid user_id type must be UUID hex for follower service - {service_name}")
                    jwt_data['user_id'] = service_user_id
                att, _rtt = ApiSdkJwt.create_jwt_pair(**jwt_data)  # type: ignore
                structure['follower_services'][service]['full_access_jwt_token'] = att.encode(private_key, self.algo)  # type: ignore
                # structure['follower_services'][service]['full_access_jwt_data'] = json.loads(json.dumps(jwt_data, cls=CustomJSONEncoder))

        # with open(os.path.join(self.dir, f'{self.env.upper()}__{self.name}__{self.algo}.private_key.pem'), 'w') as f:
        #     f.writelines(private_key.splitlines(keepends=True))
        #     write_stdout(f'   {FG_GREEN}saved:{NC} {os.path.relpath(f.name, os.getcwd())}')

        if self.env:
            result_file_name = f'{self.name}__{self.env.upper()}__{self.algo}__{datetime.now().date()}__encryption_keys.yml'
        else:
            result_file_name = f'{self.name}__{self.algo}__{datetime.now().date()}__encryption_keys.yml'

        with open(os.path.join(self.dir, result_file_name), 'w') as f:
            dump(structure, f, sort_keys=False)
            write_stdout(f'   {FG_GREEN}saved:{NC} {os.path.relpath(f.name, os.getcwd())}')

        write_stdout('')
        write_stdout(f'{FG_GREEN}DONE{NC}')
