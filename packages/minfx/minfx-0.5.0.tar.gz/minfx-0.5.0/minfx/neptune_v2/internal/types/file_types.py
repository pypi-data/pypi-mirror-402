from __future__ import annotations
__all__ = ['FileComposite', 'FileComposite', 'InMemoryComposite', 'LocalFileComposite', 'StreamComposite']
import abc
import enum
from functools import wraps
import io
from io import IOBase
from pathlib import Path
from typing import Any, Callable, TypeVar
R = TypeVar('R')
from minfx.neptune_v2.common.exceptions import NeptuneException
from minfx.neptune_v2.exceptions import StreamAlreadyUsedException
from minfx.neptune_v2.internal.utils import verify_type

class FileType(enum.Enum):
    LOCAL_FILE = 'LOCAL_FILE'
    IN_MEMORY = 'IN_MEMORY'
    STREAM = 'STREAM'

class FileComposite(abc.ABC):
    file_type: FileType = None

    def __init__(self, extension):
        verify_type('extension', extension, str)
        self._extension = extension

    @property
    def extension(self):
        return self._extension

    @property
    def path(self):
        raise NeptuneException(f'`path` attribute is not supported for {self.file_type}')

    @property
    def content(self):
        raise NeptuneException(f'`content` attribute is not supported for {self.file_type}')

    def save(self, path):
        raise NeptuneException(f'`save` method is not supported for {self.file_type}')

class LocalFileComposite(FileComposite):
    file_type = FileType.LOCAL_FILE

    def __init__(self, path, extension=None):
        try:
            ext = Path(path).suffix
            ext = ext[1:] if ext else ''
        except ValueError:
            ext = ''
        super().__init__(extension or ext)
        self._path = path

    @property
    def path(self):
        return self._path

    def __str__(self):
        return f'File(path={self.path})'

class InMemoryComposite(FileComposite):
    file_type = FileType.IN_MEMORY

    def __init__(self, content, extension=None):
        if isinstance(content, str):
            ext = 'txt'
            content = content.encode('utf-8')
        else:
            ext = 'bin'
        super().__init__(extension or ext)
        self._content = content

    @property
    def content(self):
        return self._content

    def save(self, path):
        with Path(path).open('wb') as f:
            f.write(self._content)

    def __str__(self):
        return 'File(content=...)'

def read_once(f):

    @wraps(f)
    def func(self, *args, **kwargs):
        if self._stream_read:
            raise StreamAlreadyUsedException
        self._stream_read = True
        return f(self, *args, **kwargs)
    return func

class StreamComposite(FileComposite):
    file_type = FileType.STREAM

    def __init__(self, stream, seek=0, extension=None):
        verify_type('stream', stream, (IOBase, type(None)))
        verify_type('extension', extension, (str, type(None)))
        if seek is not None and stream.seekable():
            stream.seek(seek)
        if extension is None:
            extension = 'txt' if isinstance(stream, io.TextIOBase) else 'bin'
        super().__init__(extension)
        self._stream = stream
        self._stream_read = False

    @property
    @read_once
    def content(self):
        val = self._stream.read()
        if isinstance(self._stream, io.TextIOBase):
            val = val.encode()
        return val

    @read_once
    def save(self, path):
        with Path(path).open('wb') as f:
            buffer_ = self._stream.read(io.DEFAULT_BUFFER_SIZE)
            while buffer_:
                if isinstance(self._stream, io.TextIOBase):
                    buffer_ = buffer_.encode()
                f.write(buffer_)
                buffer_ = self._stream.read(io.DEFAULT_BUFFER_SIZE)

    def __str__(self):
        return f'File(stream={self._stream})'