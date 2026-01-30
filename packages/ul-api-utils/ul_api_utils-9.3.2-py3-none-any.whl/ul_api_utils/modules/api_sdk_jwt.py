import base64
import re
from datetime import datetime, timedelta
from typing import Set, Dict, Any, NamedTuple, List, Union, Optional, Literal, Tuple, Callable, Iterable
from uuid import UUID, uuid4

import jwt

from ul_api_utils.access import PermissionDefinition
from ul_api_utils.errors import AccessApiError, PermissionDeniedApiError
from ul_api_utils.utils.json_encoder import CustomJSONEncoder

TAlgo = Union[Literal['RS256'], Literal['ES256']]
ALGORITHM__RS256: TAlgo = 'RS256'
ALGORITHM__ES256: TAlgo = 'ES256'
ALGORITHMS: List[str] = [ALGORITHM__ES256, ALGORITHM__RS256]


JWT_VERSION: str = '1'
JWT_ACCESS_TOKEN_TTL: timedelta = timedelta(hours=2)
JWT_REFRESH_TOKEN_TTL: timedelta = timedelta(days=2)


JWT_TYPE__REFRESH = 'refresh'
JTW_TYPE__ACCESS = 'access'


JWT_TYPE__COMPRESSED = {
    JWT_TYPE__REFRESH: 'r',
    JTW_TYPE__ACCESS: 'a',
}
JWT_TYPE__UNCOMPRESSED = {
    'r': JWT_TYPE__REFRESH,
    'a': JTW_TYPE__ACCESS,
}
RE_COMPRESSED_PROP = re.compile(r'^[ar](\d+)$')
JWT_EXP_DATE_TIMESTAMP_BASIS = datetime(2022, 1, 1).timestamp()

# JWT_SYMBOL_MAP_FOR_CNT = " 	ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"  # "\-
# JWT_SYMBOL_MAP_FOR_INC = "!#$%&'()*+,./:;<=>?@[]^_`{|}~¡¢£¤¥¦§¨©ª«¬®¯°±²³´µ¶·¸¹º»¼½¾¿ÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖ×ØÙÚÛÜÝÞßàáâãäåæçèéêëìíîïðñòóôõö÷øùúûüýþ"

# JWT_SYMBOL_MAP_FOR_CNT = " ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"  # "\-
# JWT_SYMBOL_MAP_FOR_INC = "!#$%&'()*+,./:;<=>?@[]^_`{|}~¡¢£¤¥¦§¨©ª«¬®¯°±²³´µ¶·¸¹º»¼½¾¿ÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖ×ØÙÚÛÜÝÞßàáâãäåæçèéêëìíîïðñòóôõö÷øùúûüýþ"

# JWT_SYMBOL_MAP_FOR_CNT = " 	!#$%&'()*+,./:;<=>?@[]^_`{|}~"  # "\-
# JWT_SYMBOL_MAP_FOR_INC = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"

JWT_SYMBOL_MAP_FOR_CNT = " !#$%&'()*+,./:;<=>?@[]^_`{|}~"  # "\-
JWT_SYMBOL_MAP_FOR_INC = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
assert len(JWT_SYMBOL_MAP_FOR_INC) == len(set(JWT_SYMBOL_MAP_FOR_INC))
assert len(JWT_SYMBOL_MAP_FOR_CNT) == len(set(JWT_SYMBOL_MAP_FOR_CNT))
assert not set(JWT_SYMBOL_MAP_FOR_CNT).intersection(set(JWT_SYMBOL_MAP_FOR_INC))
assert not set(JWT_SYMBOL_MAP_FOR_INC).intersection(set(JWT_SYMBOL_MAP_FOR_CNT))


class ApiSdkJwt(NamedTuple):
    id: UUID
    user_id: UUID
    organization_id: Optional[UUID]
    version: str
    token_type: str
    exp_date: datetime
    env: str
    permissions: Set[int]
    additional_data: Dict[str, Any]
    is_superuser: Optional[bool] = False
    raw: Optional[str] = None
    username: Optional[str] = None

    @staticmethod
    def load_cert(certificate: str) -> Tuple[str, Callable[[], str]]:
        from cryptography.hazmat.primitives import serialization

        private_key = serialization.load_pem_private_key(
            certificate.encode('utf-8'),
            password=None,
        )

        def pub_key_factory() -> str:
            public_key = private_key.public_key()
            serialized_public = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
            return serialized_public.decode('utf-8')

        return (
            certificate,
            pub_key_factory,
        )

    @staticmethod
    def generate_cert(algorithm: TAlgo) -> Tuple[str, Callable[[], str]]:
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import ec
        from cryptography.hazmat.primitives.asymmetric import rsa

        assert algorithm in ALGORITHMS, f'algorithm {algorithm} is not supported'
        if algorithm == ALGORITHM__ES256:
            private_key = ec.generate_private_key(ec.SECP384R1())
        elif algorithm == ALGORITHM__RS256:
            private_key = rsa.generate_private_key(65537, 2048)  # type: ignore

        def pub_key_factory() -> str:
            public_key = private_key.public_key()
            serialized_public = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
            return serialized_public.decode('utf-8')

        return (
            private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            ).decode('utf-8'),
            pub_key_factory,
        )

    def encode(self, certificate: str, algorithm: TAlgo, compressed: bool = False) -> str:
        assert algorithm in ALGORITHMS
        if not isinstance(certificate, str):
            raise TypeError(f'invalid type of config.jwt_private_key. must be str. {type(certificate).__name__} was given')

        if compressed:
            data: Dict[str, Any] = {
                f'{JWT_TYPE__COMPRESSED[self.token_type]}{self.version}': [
                    self.env,  # env
                    self.compress_uuid(self.id),  # id
                    self.compress_uuid(self.user_id),  # user_id
                    self.compress_uuid(self.organization_id) if self.organization_id else '',  # organization_id
                    self.is_superuser,
                    int((self.exp_date.timestamp() - JWT_EXP_DATE_TIMESTAMP_BASIS) / 60),  # exp_date IN MINUTES
                    self.compress_permissions(self.permissions),  # permissions
                ],
                **self.additional_data,
            }
        else:
            data = dict(
                id=str(self.id),
                user_id=str(self.user_id),
                organization_id=str(self.organization_id) if self.organization_id is not None else None,
                is_superuser=self.is_superuser,
                version=str(self.version),
                token_type=self.token_type,
                exp_date=self.exp_date.isoformat(),
                env=self.env,
                permissions=list(self.permissions),
                **self.additional_data,
            )
        return jwt.encode(data, certificate, algorithm=algorithm, json_encoder=CustomJSONEncoder)

    @classmethod
    def decode(cls, token: str, certificate: str, username: Optional[str] = None) -> 'ApiSdkJwt':
        data = jwt.decode(token, certificate, algorithms=ALGORITHMS)
        compressed_props = [k for k in data.keys() if RE_COMPRESSED_PROP.match(k) is not None]

        if len(compressed_props) == 1:  # COMPRESSED
            comp_key = compressed_props[0]
            values = data.pop(comp_key)
            token_type = JWT_TYPE__UNCOMPRESSED[comp_key[0]]
            version = int(comp_key[1:])

            if not isinstance(values, (list, tuple)):
                raise TypeError('invalid compressed token payload')

            if len(values) == 7:
                env, _id, _user_id, _organization_id, _is_superuser, _exp_date, _permissions = values
            elif len(values) == 6:
                env, _id, _user_id, _organization_id, _exp_date, _permissions = values
                _is_superuser = False
            else:
                raise TypeError(f'unexpected compressed token payload length: {len(values)}')

            # Convert values to expected types
            id = cls.decompress_uuid(_id)
            user_id = cls.decompress_uuid(_user_id)
            organization_id = cls.decompress_uuid(_organization_id) if len(_organization_id) > 0 else None
            is_superuser = bool(_is_superuser)
            exp_date = datetime.fromtimestamp(JWT_EXP_DATE_TIMESTAMP_BASIS + _exp_date * 60)
            permissions = set(sorted(cls.decompress_permissions(_permissions)))
        else:
            # print('1>>>', json.dumps(list(sorted(data['permissions'])), separators=(',', ':')))
            id = UUID(data.pop('id'))
            env = data.pop('env')
            exp_date = datetime.fromisoformat(data.pop('exp_date'))
            version = int(data.pop('version'))
            token_type = data.pop('token_type')
            user_id = UUID(data.pop('user_id'))
            organization_id = UUID(data.pop('organization_id')) if data.get('organization_id', None) is not None else None
            is_superuser = bool(data.pop('is_superuser')) if 'is_superuser' in data else False
            permissions = set(sorted(data.pop('permissions')))

        if not isinstance(env, str):
            raise TypeError('invalid type of env')

        if not isinstance(token_type, str):
            raise TypeError('invalid type of token_type')

        return ApiSdkJwt(
            id=id,
            env=env,
            token_type=token_type,
            exp_date=exp_date,
            version=str(version),
            user_id=user_id,
            organization_id=organization_id,
            is_superuser=is_superuser,
            permissions=permissions,
            additional_data=data,
            username=username,
            raw=token,
        )

    def ensure_organization_id(self) -> UUID:
        if self.organization_id is None:
            raise PermissionDeniedApiError('you must be logged in some organisation')
        return self.organization_id

    @property
    def is_expired(self) -> bool:
        return self.exp_date < datetime.now()

    @property
    def is_refresh_token(self) -> bool:
        return self.token_type == JWT_TYPE__REFRESH

    @property
    def is_access_token(self) -> bool:
        return self.token_type == JTW_TYPE__ACCESS

    def has_permission(self, permission: Union[PermissionDefinition, int]) -> bool:
        if isinstance(permission, int):
            return permission in self.permissions

        if isinstance(permission, PermissionDefinition):
            return permission.id in self.permissions

        raise TypeError('invalid permission type')

    @staticmethod
    def create_jwt_pair(
        *,
        environment: str,
        user_id: Union[str, UUID],
        organization_id: Optional[Union[str, UUID]],
        permissions: List[Union[int, PermissionDefinition]],
        is_superuser: Optional[bool] = False,
        access_expiration_date: Optional[datetime] = None,
        refresh_expiration_date: Optional[datetime] = None,
        additional_data: Optional[Dict[str, Any]] = None,
    ) -> Tuple['ApiSdkJwt', 'ApiSdkJwt']:
        if additional_data is None:
            additional_data = dict()
        id = uuid4()
        now = datetime.now()

        user_id = user_id if isinstance(user_id, UUID) else UUID(user_id)
        if organization_id is not None:
            organization_id = organization_id if isinstance(organization_id, UUID) else UUID(organization_id)

        at = ApiSdkJwt(
            id=id,
            env=str(environment),
            version=JWT_VERSION,
            user_id=user_id,
            organization_id=organization_id,
            is_superuser=is_superuser,
            permissions={(p if isinstance(p, int) else p.id) for p in permissions},
            additional_data=additional_data,
            token_type=JTW_TYPE__ACCESS,
            exp_date=access_expiration_date or (now + JWT_ACCESS_TOKEN_TTL),
        )
        rt = ApiSdkJwt(
            id=id,
            env=str(environment),
            version=JWT_VERSION,
            user_id=user_id,
            organization_id=organization_id,
            is_superuser=is_superuser,
            permissions={(p if isinstance(p, int) else p.id) for p in permissions},
            additional_data=additional_data,
            token_type=JWT_TYPE__REFRESH,
            exp_date=refresh_expiration_date or (now + JWT_REFRESH_TOKEN_TTL),
        )
        return at, rt

    def create_access_token(self, expiration_date: Optional[datetime] = None) -> 'ApiSdkJwt':
        if not self.is_refresh_token:
            raise AccessApiError('invalid token type')

        exp_date = expiration_date if expiration_date is not None else min(datetime.now() + JWT_ACCESS_TOKEN_TTL, self.exp_date)

        if exp_date > self.exp_date:
            exp_date = self.exp_date

        return ApiSdkJwt(
            id=self.id,
            env=self.env,
            version=self.version,
            user_id=self.user_id,
            organization_id=self.organization_id,
            is_superuser=self.is_superuser,
            permissions=self.permissions,
            token_type=JTW_TYPE__ACCESS,
            exp_date=exp_date,
            additional_data=self.additional_data,
        )

    @classmethod
    def compress_uuid(cls, id: UUID) -> str:
        # return "".join(chr(i+10) for i in id.bytes)
        # return str(id.int)
        return base64.b85encode(id.bytes).decode('utf-8')

    @classmethod
    def decompress_uuid(cls, id: str) -> UUID:
        return UUID(bytes=base64.b85decode(id))

    @classmethod
    def compress_permissions(cls, permissions: Iterable[int]) -> str:
        permissions = list(sorted(set(permissions)))
        if len(permissions) == 0:
            return ''
        if len(permissions) == 1:
            return str(permissions[0])
        res_permissions: List[Tuple[int, int]] = []
        prev_p: Optional[int] = None
        for p in permissions:
            if prev_p is None:
                res_permissions.append((p, 1))
            else:
                prev_inc, prev_cnt = res_permissions[-1]
                cur_inc = p - prev_p
                if prev_inc == cur_inc:
                    res_permissions[-1] = prev_inc, prev_cnt + 1
                else:
                    res_permissions.append((cur_inc, 1))
            prev_p = p
        res = ''
        for v, c in res_permissions:
            res += sorted((i for i in (cls._compress_v1(v, c), cls._compress_v2(v, c)) if len(i)), key=len)[0]
        res = res.strip()
        return res

    @classmethod
    def _compress_v1(cls, v: int, c: int) -> str:
        l_cnt = len(JWT_SYMBOL_MAP_FOR_CNT)
        # return f'{JWT_SYMBOL_MAP_FOR_CNT[-1] * (c // l_cnt)}{JWT_SYMBOL_MAP_FOR_CNT[(c % l_cnt) - 1] if c % l_cnt != 0 else ""}{v}'
        return (
            f'{JWT_SYMBOL_MAP_FOR_CNT[-1] * (c // l_cnt)}{JWT_SYMBOL_MAP_FOR_CNT[(c % l_cnt) - 1] if c % l_cnt != 0 else ""}'
            f'{v if v < 10 or (v - 9 > len(JWT_SYMBOL_MAP_FOR_INC)) else JWT_SYMBOL_MAP_FOR_INC[v -1 - 9]}'
        )

    @classmethod
    def _compress_v2(cls, v: int, c: int) -> str:
        if v > len(JWT_SYMBOL_MAP_FOR_INC):
            return ''
        return f"{JWT_SYMBOL_MAP_FOR_INC[v - 1]}{c if c != 1 else ''}"

    @classmethod
    def decompress_permissions(cls, permissions: str) -> List[int]:
        if not permissions:
            return []
        res_permissions: List[int] = []
        for c, v in re.compile(r'(\D+)(\d*)').findall(f' {permissions}' if permissions[0] in '123456789' else permissions):
            res: List[Tuple[int, int]] = []
            cur_grp = ''
            for i, ci in enumerate(c):
                i_last = i == (len(c) - 1)
                if ci in JWT_SYMBOL_MAP_FOR_CNT:
                    cur_grp += ci
                else:
                    if len(cur_grp):
                        cii_v = JWT_SYMBOL_MAP_FOR_INC.find(ci) + 1 + 9
                        for cii in cur_grp:
                            res.append((cii_v, JWT_SYMBOL_MAP_FOR_CNT.find(cii) + 1))
                        cur_grp = ''
                    else:
                        res.append((JWT_SYMBOL_MAP_FOR_INC.find(ci) + 1, 1 if (len(v) == 0) or not i_last else int(v)))
                if i_last and len(cur_grp):
                    for cii in cur_grp:
                        res.append((1 if len(v) == 0 else int(v), JWT_SYMBOL_MAP_FOR_CNT.find(cii) + 1))
                    cur_grp = ''
            for val, cnt in res:
                for _i in range(cnt):
                    res_permissions.append(res_permissions[-1] + val if res_permissions else val)
        return res_permissions
