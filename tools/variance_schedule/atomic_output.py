"""Atomic file replacement helpers."""

import os
import secrets
from pathlib import Path


def atomic_write(path, writer):
    """Write binary content to a same-directory temporary, then replace path."""
    path = Path(path)
    temp_path = None
    fd = None
    try:
        while True:
            candidate = path.parent / f".{path.name}.{secrets.token_hex(16)}.tmp"
            try:
                fd = os.open(candidate, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o666)
            except FileExistsError:
                continue
            temp_path = candidate
            break

        with os.fdopen(fd, "wb") as stream:
            fd = None
            writer(stream)
        os.replace(temp_path, path)
        temp_path = None
    finally:
        if fd is not None:
            os.close(fd)
        if temp_path is not None:
            try:
                os.unlink(temp_path)
            except FileNotFoundError:
                pass
