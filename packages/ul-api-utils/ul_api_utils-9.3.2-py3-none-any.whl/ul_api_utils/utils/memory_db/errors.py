class CompositeKeyError(LookupError):
    """Raised in memory db repository when composite key is invalid."""
    ...


class UnsupportedParsingType(TypeError):
    """Raised in memory db repository when repo can't parse memory db object as provided type."""
    ...
