from __future__ import annotations
import abc
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Generic, TypeVar
from minfx.neptune_v2.common.exceptions import InternalClientError, NeptuneException
from minfx.neptune_v2.exceptions import MalformedOperation
from minfx.neptune_v2.internal.container_type import ContainerType
from minfx.neptune_v2.internal.types.file_types import FileType
Ret = TypeVar('Ret')
T = TypeVar('T')

def all_subclasses(cls):
    return set(cls.__subclasses__()).union([s for c in cls.__subclasses__() for s in all_subclasses(c)])

@dataclass
class Operation(abc.ABC):
    path: list[str]

    @abc.abstractmethod
    def accept(self, visitor):
        pass

    def clean(self, operation_storage):
        pass

    def to_dict(self):
        return {'type': self.__class__.__name__, 'path': self.path}

    @staticmethod
    def from_dict(data):
        if 'type' not in data:
            raise ValueError(f'Malformed operation {data} - type is missing')
        sub_classes = {cls.__name__: cls for cls in all_subclasses(Operation)}
        if data['type'] not in sub_classes:
            msg = 'Malformed operation {} - unknown type {}'.format(data, data['type'])
            raise ValueError(msg)
        return sub_classes[data['type']].from_dict(data)

@dataclass
class AssignFloat(Operation):
    value: float

    def accept(self, visitor):
        return visitor.visit_assign_float(self)

    def to_dict(self):
        ret = super().to_dict()
        ret['value'] = self.value
        return ret

    @staticmethod
    def from_dict(data):
        return AssignFloat(data['path'], data['value'])

@dataclass
class AssignInt(Operation):
    value: int

    def accept(self, visitor):
        return visitor.visit_assign_int(self)

    def to_dict(self):
        ret = super().to_dict()
        ret['value'] = self.value
        return ret

    @staticmethod
    def from_dict(data):
        return AssignInt(data['path'], data['value'])

@dataclass
class AssignBool(Operation):
    value: bool

    def accept(self, visitor):
        return visitor.visit_assign_bool(self)

    def to_dict(self):
        ret = super().to_dict()
        ret['value'] = self.value
        return ret

    @staticmethod
    def from_dict(data):
        return AssignBool(data['path'], data['value'])

@dataclass
class AssignString(Operation):
    value: str

    def accept(self, visitor):
        return visitor.visit_assign_string(self)

    def to_dict(self):
        ret = super().to_dict()
        ret['value'] = self.value
        return ret

    @staticmethod
    def from_dict(data):
        return AssignString(data['path'], data['value'])

@dataclass
class AssignDatetime(Operation):
    value: datetime

    def accept(self, visitor):
        return visitor.visit_assign_datetime(self)

    def to_dict(self):
        ret = super().to_dict()
        ret['value'] = int(1000 * self.value.timestamp())
        return ret

    @staticmethod
    def from_dict(data):
        return AssignDatetime(data['path'], datetime.fromtimestamp(data['value'] / 1000))

@dataclass
class AssignArtifact(Operation):
    hash: str

    def accept(self, visitor):
        return visitor.visit_assign_artifact(self)

    def to_dict(self):
        ret = super().to_dict()
        ret['hash'] = self.hash
        return ret

    @staticmethod
    def from_dict(data):
        return AssignArtifact(data['path'], str(data['hash']))

@dataclass
class UploadFile(Operation):
    ext: str
    file_path: str = None
    tmp_file_name: str = None
    clean_after_upload: bool = False

    @classmethod
    def of_file(cls, value, attribute_path, operation_storage):
        if value.file_type is FileType.LOCAL_FILE:
            operation = UploadFile(path=attribute_path, ext=value.extension, file_path=str(Path(value.path).resolve()))
        elif value.file_type in (FileType.IN_MEMORY, FileType.STREAM):
            tmp_file_name = cls.get_tmp_file_name(attribute_path, value.extension)
            value._save(operation_storage.upload_path / tmp_file_name)
            operation = UploadFile(path=attribute_path, ext=value.extension, tmp_file_name=tmp_file_name)
        else:
            raise ValueError(f'Unexpected FileType: {value.file_type}')
        return operation

    def clean(self, operation_storage):
        if self.clean_after_upload or self.tmp_file_name:
            Path(self.get_absolute_path(operation_storage)).unlink()

    def accept(self, visitor):
        return visitor.visit_upload_file(self)

    def to_dict(self):
        ret = super().to_dict()
        ret['ext'] = self.ext
        ret['file_path'] = self.file_path
        ret['tmp_file_name'] = self.tmp_file_name
        ret['clean_after_upload'] = self.clean_after_upload
        return ret

    @staticmethod
    def from_dict(data):
        return UploadFile(data['path'], data['ext'], data.get('file_path'), data.get('tmp_file_name'), data.get('clean_after_upload', False))

    @staticmethod
    def get_tmp_file_name(attribute_path, extension):
        now = datetime.now(tz=timezone.utc)
        tmp_file_name = f"{'_'.join(attribute_path)}-{now.timestamp()}-{now.strftime('%Y-%m-%d_%H.%M.%S.%f')}.{extension}"
        return tmp_file_name

    def get_absolute_path(self, operation_storage):
        if self.file_path:
            return self.file_path
        if self.tmp_file_name:
            return str(operation_storage.upload_path / self.tmp_file_name)
        raise NeptuneException("Expected 'file_path' or 'tmp_file_name' to be filled.")

@dataclass
class UploadFileContent(Operation):
    ext: str
    file_content: str

    def accept(self, visitor):
        return visitor.visit_upload_file_content(self)

    def to_dict(self):
        ret = super().to_dict()
        ret['ext'] = self.ext
        ret['file_content'] = self.file_content
        return ret

    @staticmethod
    def from_dict(data):
        return UploadFileContent(data['path'], data['ext'], data['file_content'])

@dataclass
class UploadFileSet(Operation):
    file_globs: list[str]
    reset: bool

    def accept(self, visitor):
        return visitor.visit_upload_file_set(self)

    def to_dict(self):
        ret = super().to_dict()
        ret['file_globs'] = self.file_globs
        ret['reset'] = str(self.reset)
        return ret

    @staticmethod
    def from_dict(data):
        return UploadFileSet(data['path'], data['file_globs'], data['reset'] != str(False))

class LogOperation(Operation, abc.ABC):
    pass

@dataclass
class LogSeriesValue(Generic[T]):
    value: T
    step: float | None
    ts: float

    def to_dict(self, value_serializer=lambda x: x):
        return {'value': value_serializer(self.value), 'step': self.step, 'ts': self.ts}

    @staticmethod
    def from_dict(data, value_deserializer=lambda x: x):
        return LogSeriesValue[T](value_deserializer(data['value']), data.get('step'), data['ts'])

@dataclass
class LogFloats(LogOperation):
    ValueType = LogSeriesValue[float]
    values: list[ValueType]

    def accept(self, visitor):
        return visitor.visit_log_floats(self)

    def to_dict(self):
        ret = super().to_dict()
        ret['values'] = [value.to_dict() for value in self.values]
        return ret

    @staticmethod
    def from_dict(data):
        return LogFloats(data['path'], [LogFloats.ValueType.from_dict(value) for value in data['values']])

@dataclass
class LogStrings(LogOperation):
    ValueType = LogSeriesValue[str]
    values: list[ValueType]

    def accept(self, visitor):
        return visitor.visit_log_strings(self)

    def to_dict(self):
        ret = super().to_dict()
        ret['values'] = [value.to_dict() for value in self.values]
        return ret

    @staticmethod
    def from_dict(data):
        return LogStrings(data['path'], [LogStrings.ValueType.from_dict(value) for value in data['values']])

@dataclass
class ImageValue:
    data: str | None
    name: str | None
    description: str | None

    @staticmethod
    def serializer(obj):
        return {'data': obj.data, 'name': obj.name, 'description': obj.description}

    @staticmethod
    def deserializer(obj):
        if obj is None:
            return ImageValue(None, None, None)
        if isinstance(obj, str):
            return ImageValue(data=obj, name=None, description=None)
        if isinstance(obj, dict):
            return ImageValue(data=obj['data'], name=obj['name'], description=obj['description'])
        raise InternalClientError('Run data on disk is malformed or was saved by newer version of Neptune Library')

@dataclass
class LogImages(LogOperation):
    ValueType = LogSeriesValue[ImageValue]
    values: list[ValueType]

    def accept(self, visitor):
        return visitor.visit_log_images(self)

    def to_dict(self):
        ret = super().to_dict()
        ret['values'] = [value.to_dict(ImageValue.serializer) for value in self.values]
        return ret

    @staticmethod
    def from_dict(data):
        return LogImages(data['path'], [LogImages.ValueType.from_dict(value, ImageValue.deserializer) for value in data['values']])

@dataclass
class ClearFloatLog(Operation):

    def accept(self, visitor):
        return visitor.visit_clear_float_log(self)

    @staticmethod
    def from_dict(data):
        return ClearFloatLog(data['path'])

@dataclass
class ClearStringLog(Operation):

    def accept(self, visitor):
        return visitor.visit_clear_string_log(self)

    @staticmethod
    def from_dict(data):
        return ClearStringLog(data['path'])

@dataclass
class ClearImageLog(Operation):

    def accept(self, visitor):
        return visitor.visit_clear_image_log(self)

    @staticmethod
    def from_dict(data):
        return ClearImageLog(data['path'])

@dataclass
class ConfigFloatSeries(Operation):
    min: float | None
    max: float | None
    unit: str | None

    def accept(self, visitor):
        return visitor.visit_config_float_series(self)

    def to_dict(self):
        ret = super().to_dict()
        ret['min'] = self.min
        ret['max'] = self.max
        ret['unit'] = self.unit
        return ret

    @staticmethod
    def from_dict(data):
        return ConfigFloatSeries(data['path'], data['min'], data['max'], data['unit'])

@dataclass
class AddStrings(Operation):
    values: set[str]

    def accept(self, visitor):
        return visitor.visit_add_strings(self)

    def to_dict(self):
        ret = super().to_dict()
        ret['values'] = list(self.values)
        return ret

    @staticmethod
    def from_dict(data):
        return AddStrings(data['path'], set(data['values']))

@dataclass
class RemoveStrings(Operation):
    values: set[str]

    def accept(self, visitor):
        return visitor.visit_remove_strings(self)

    def to_dict(self):
        ret = super().to_dict()
        ret['values'] = list(self.values)
        return ret

    @staticmethod
    def from_dict(data):
        return RemoveStrings(data['path'], set(data['values']))

@dataclass
class ClearStringSet(Operation):

    def accept(self, visitor):
        return visitor.visit_clear_string_set(self)

    @staticmethod
    def from_dict(data):
        return ClearStringSet(data['path'])

@dataclass
class DeleteFiles(Operation):
    file_paths: set[str]

    def accept(self, visitor):
        return visitor.visit_delete_files(self)

    def to_dict(self):
        ret = super().to_dict()
        ret['file_paths'] = list(self.file_paths)
        return ret

    @staticmethod
    def from_dict(data):
        return DeleteFiles(data['path'], set(data['file_paths']))

@dataclass
class DeleteAttribute(Operation):

    def accept(self, visitor):
        return visitor.visit_delete_attribute(self)

    @staticmethod
    def from_dict(data):
        return DeleteAttribute(data['path'])

@dataclass
class TrackFilesToArtifact(Operation):
    project_id: str
    entries: list[tuple[str, str | None]]

    def accept(self, visitor):
        return visitor.visit_track_files_to_artifact(self)

    def to_dict(self):
        ret = super().to_dict()
        ret['entries'] = self.entries
        ret['project_id'] = self.project_id
        return ret

    @staticmethod
    def from_dict(data):
        return TrackFilesToArtifact(path=data['path'], project_id=data['project_id'], entries=list(map(tuple, data['entries'])))

@dataclass
class ClearArtifact(Operation):

    def accept(self, visitor):
        return visitor.visit_clear_artifact(self)

    @staticmethod
    def from_dict(data):
        return ClearArtifact(data['path'])

@dataclass
class CopyAttribute(Operation):
    container_id: str
    container_type: ContainerType
    source_path: list[str]
    source_attr_cls: type[Attribute]

    def accept(self, visitor):
        return visitor.visit_copy_attribute(self)

    def to_dict(self):
        ret = super().to_dict()
        ret['container_id'] = self.container_id
        ret['container_type'] = self.container_type.value
        ret['source_path'] = self.source_path
        ret['source_attr_name'] = self.source_attr_cls.__name__
        return ret

    @staticmethod
    def from_dict(data):
        from minfx.neptune_v2.attributes.attribute import Attribute
        source_attr_cls = {cls.__name__: cls for cls in all_subclasses(Attribute) if cls.supports_copy}.get(data['source_attr_name'])
        if source_attr_cls is None:
            raise MalformedOperation('Copy of non-copiable type found in queue!')
        return CopyAttribute(data['path'], data['container_id'], ContainerType(data['container_type']), data['source_path'], source_attr_cls)

    def resolve(self, backend):
        getter = self.source_attr_cls.getter
        create_assignment_operation = self.source_attr_cls.create_assignment_operation
        value = getter(backend, self.container_id, self.container_type, self.source_path)
        return create_assignment_operation(self.path, value)