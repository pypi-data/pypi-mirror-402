from __future__ import annotations
__all__ = ['ArtifactDriver', 'ArtifactDriversMap', 'ArtifactFileData', 'ArtifactFileType', 'ArtifactMetadataSerializer']
import abc
from dataclasses import dataclass
import enum
import typing
from minfx.neptune_v2.exceptions import NeptuneUnhandledArtifactSchemeException, NeptuneUnhandledArtifactTypeException

class ArtifactFileType(enum.Enum):
    S3 = 'S3'
    LOCAL = 'Local'

class ArtifactMetadataSerializer:

    @staticmethod
    def serialize(metadata):
        return [{'key': k, 'value': v} for k, v in sorted(metadata.items())]

    @staticmethod
    def deserialize(metadata):
        return {f"{key_value.get('key')}": f"{key_value.get('value')}" for key_value in metadata}

@typing.runtime_checkable
class ArtifactFileDTO(typing.Protocol):

    @property
    def filePath(self):
        ...

    @property
    def fileHash(self):
        ...

    @property
    def type(self):
        ...

    @property
    def size(self):
        ...

    @property
    def metadata(self):
        ...

@dataclass
class ArtifactFileData:
    file_path: str
    file_hash: str
    type: str
    metadata: dict[str, str]
    size: int | None = None

    @classmethod
    def from_dto(cls, artifact_file_dto):
        return cls(file_path=artifact_file_dto.filePath, file_hash=artifact_file_dto.fileHash, type=artifact_file_dto.type, size=artifact_file_dto.size, metadata=ArtifactMetadataSerializer.deserialize([{'key': str(m.key), 'value': str(m.value)} for m in artifact_file_dto.metadata]))

    def to_dto(self):
        return {'filePath': self.file_path, 'fileHash': self.file_hash, 'type': self.type, 'size': self.size, 'metadata': ArtifactMetadataSerializer.serialize(self.metadata)}

class ArtifactDriversMap:
    _implementations: list[type[ArtifactDriver]] = []

    @classmethod
    def match_path(cls, path):
        for artifact_driver in cls._implementations:
            if artifact_driver.matches(path):
                return artifact_driver
        raise NeptuneUnhandledArtifactSchemeException(path)

    @classmethod
    def match_type(cls, type_str):
        for artifact_driver in cls._implementations:
            if artifact_driver.get_type() == type_str:
                return artifact_driver
        raise NeptuneUnhandledArtifactTypeException(type_str)

class ArtifactDriver(abc.ABC):

    def __init_subclass__(cls):
        ArtifactDriversMap._implementations.append(cls)

    @staticmethod
    def get_type():
        raise NotImplementedError

    @classmethod
    def matches(cls, path):
        raise NotImplementedError

    @classmethod
    def get_tracked_files(cls, path, destination=None):
        raise NotImplementedError

    @classmethod
    def download_file(cls, destination, file_definition):
        raise NotImplementedError