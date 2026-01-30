import re
from typing import Dict, List, Union, Any, Iterable

from pydantic import ConfigDict, BaseModel

from ul_api_utils.conf import APPLICATION_F


class PermissionDefinition(BaseModel):
    id: int
    key: str
    name: str
    category: str
    flags: str = ''

    model_config = ConfigDict(frozen=True)


class PermissionRegistry:
    """
    Examples:
        reg = PermissionRegistry('some_service_name', 10000, 10100)
        PII_GET_USER = reg.add(PermissionDefinition.new('PII_GET_USER', 1, 'permission get user', 'user'))
    """

    __slots__ = (
        '_service_name',
        '_index_by_id',
        '_index_by_key',
        '_index_by_category',
        '_permission_ids',
        '_categories',
        '_start_id',
        '_end_id',
    )

    def __init__(self, service_name: str, start_id: int, end_id: int) -> None:
        self._service_name = service_name
        self._index_by_id: Dict[int, PermissionDefinition] = dict()
        self._index_by_key: Dict[str, PermissionDefinition] = dict()
        self._index_by_category: Dict[str, List[PermissionDefinition]] = dict()
        self._permission_ids: List[int] = list()
        self._categories: List[str] = list()

        self._start_id = start_id
        self._end_id = end_id

    @staticmethod
    def get_ids_from_iterable(permissions: Iterable[PermissionDefinition]) -> List[int]:
        return [p.id for p in permissions]

    def has(self, permission: Union[int, PermissionDefinition]) -> bool:
        return (permission.id if isinstance(permission, PermissionDefinition) else permission) in self._index_by_id

    def add(self, key: str, id: int, name: str, category: str, flags: str = '') -> PermissionDefinition:
        assert isinstance(id, int), f"id must be int. {type(id)} given"
        assert isinstance(name, str), f"name must be str. {type(name)} given"
        assert isinstance(key, str), f"key must be str. {type(key)} given"
        assert isinstance(category, str), f"category must be str. {type(category)} given"

        id = self._start_id + id  # BECAUSE BASE COULD BE CHANGED

        assert id not in {GLOBAL_PERMISSION__PRIVATE.id, GLOBAL_PERMISSION__PUBLIC.id, GLOBAL_PERMISSION__PRIVATE_RT.id}

        if id in self._index_by_id:
            raise ValueError(f'duplicate id={id}')
        if key in self._index_by_key:
            raise ValueError(f'duplicate key={key}')
        if id > self._end_id:
            raise ValueError(f'permission id={id} > {self._end_id}')
        if id < self._start_id:
            raise ValueError(f'permission id={id} < {self._end_id}')
        if not re.match(r'^[A-Z][A-Z0-9_]+[A-Z0-9]$', key):
            raise ValueError('key has invalid template')

        permission = PermissionDefinition(
            id=id,
            key=key,
            name=name,
            category=category,
            flags=flags,
        )

        self._permission_ids.append(id)

        self._index_by_id[id] = permission
        self._index_by_key[key] = permission

        if category not in self._index_by_category:
            self._index_by_category[category] = list()
            self._categories.append(category)
        self._index_by_category[category].append(permission)

        return permission

    def get_categories_with_permissions(self) -> List[Dict[str, Union[str, List[Dict[str, Union[int, str]]]]]]:
        result: List[Dict[str, Any]] = []
        for c in self._categories:
            perms = []
            for p in self._index_by_category[c]:
                if not p.flags or APPLICATION_F.has_or_unset(p.flags):
                    perms.append(dict(id=p.id, name=p.name, key=p.key))
            result.append(dict(
                category=c,
                service=self._service_name,
                permissions=perms,
            ))
        return result

    def get_permissions_ids(self) -> List[int]:
        return self._permission_ids

    def get_categories(self) -> List[str]:
        return self._categories

    def get_permissions_ids_of_category(self, category: str) -> List[int]:
        return [p.id for p in self._index_by_category[category]]


GLOBAL_PERMISSION__PUBLIC = PermissionDefinition(id=0, key='PUBLIC', name='public access', category='')
GLOBAL_PERMISSION__PRIVATE = PermissionDefinition(id=1, key='PRIVATE_AT', name='user must be logged in', category='')
GLOBAL_PERMISSION__PRIVATE_RT = PermissionDefinition(id=2, key='PRIVATE_RT', name='user must be logged in and resource must check only refresh token', category='')
