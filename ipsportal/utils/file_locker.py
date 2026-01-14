"""Manage locks on files so they cannot be accessed concurrently"""

import os
import sys
import time
from typing import IO, Any


def _portable_lock_fsize(fd: IO[Any]) -> int:
    return os.path.getsize(os.path.realpath(fd.name))


if sys.platform == 'win32':
    import msvcrt

    # lock/unlock the entire file

    def _portable_lock(fd: IO[Any]) -> None:
        fd.seek(0)
        msvcrt.locking(fd.fileno(), msvcrt.LK_LOCK, _portable_lock_fsize(fd))

    def _portable_unlock(fd: IO[Any]) -> None:
        fd.seek(0)
        msvcrt.locking(fd.fileno(), msvcrt.LK_UNLCK, _portable_lock_fsize(fd))
else:
    import fcntl

    def _portable_lock(fd: IO[Any]) -> None:
        fcntl.flock(fd.fileno(), fcntl.LOCK_EX)

    def _portable_unlock(fd: IO[Any]) -> None:
        fcntl.flock(fd.fileno(), fcntl.LOCK_UN)


class FileLocker:
    """
    Cross-platform way to acquire a file lock for concurrent calls. Note that calling the constructor is a blocking call

    use "timeout" to determine how long the function should block. Raises OSError if timeout exceeded.
    """

    def __init__(self, fd: IO[Any], timeout: float = 30.0) -> None:
        self.fd = fd
        start_time = time.time()
        while time.time() < start_time + timeout:
            try:
                _portable_lock(self.fd)
            except OSError:
                time.sleep(0.05)
            else:
                return

        msg = f'Unable to secure file lock for {fd.name}'
        raise OSError(msg)

    def __enter__(self) -> IO[Any]:
        return self.fd

    def __exit__(self, _type: object, value: object, tb: object) -> None:
        try:
            _portable_unlock(self.fd)
        finally:
            self.fd.close()
