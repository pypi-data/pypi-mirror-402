from enum import Enum


class SchemaType(Enum):
    """
    Class SchemaType: Enum for types of schema types
    """

    LIST = 'LIST'
    MARSH_MALLOW = 'MARSH_MALLOW'
    DICT = 'DICT'
    STRING = 'STRING'

    def __repr__(self) -> str:
        return f'{type(self).__name__}.{self.name}'
