import functools
import hashlib


class Flagged:
    def __init__(self, flags: str) -> None:
        self._flsgs = set(_feature.strip() for _feature in flags.strip().upper().split(',') if len(_feature.strip()))

    @functools.cache  # noqa: B019
    def has_or_unset(self, flag: str) -> bool:
        flags = set(_feature.strip() for _feature in flag.strip().upper().split(',') if len(_feature.strip()))
        if not len(flags):
            return True
        for f in flags:
            if f in self._flsgs:
                return True
            fh = hashlib.sha1()
            fh.update(f.encode())
            if fh.digest().hex().upper() in self._flsgs:
                return True
        return False

    def gen_hashed(self) -> str:
        res_flags = []
        for f in self._flsgs:
            fh = hashlib.sha1()
            fh.update(f.encode())
            res_flags.append(fh.digest().hex().upper())
        return ",".join(res_flags)
