from __future__ import annotations
__all__ = ['ValueToAttributeVisitor']
from typing import TYPE_CHECKING
from minfx.neptune_v2.attributes.atoms.artifact import Artifact as ArtifactAttr
from minfx.neptune_v2.attributes.atoms.boolean import Boolean as BooleanAttr
from minfx.neptune_v2.attributes.atoms.datetime import Datetime as DatetimeAttr
from minfx.neptune_v2.attributes.atoms.file import File as FileAttr
from minfx.neptune_v2.attributes.atoms.float import Float as FloatAttr
from minfx.neptune_v2.attributes.atoms.integer import Integer as IntegerAttr
from minfx.neptune_v2.attributes.atoms.string import String as StringAttr
from minfx.neptune_v2.attributes.attribute import Attribute
from minfx.neptune_v2.attributes.file_set import FileSet as FileSetAttr
from minfx.neptune_v2.attributes.namespace import Namespace as NamespaceAttr
from minfx.neptune_v2.attributes.series.file_series import FileSeries as ImageSeriesAttr
from minfx.neptune_v2.attributes.series.float_series import FloatSeries as FloatSeriesAttr
from minfx.neptune_v2.attributes.series.string_series import StringSeries as StringSeriesAttr
from minfx.neptune_v2.attributes.sets.string_set import StringSet as StringSetAttr
from minfx.neptune_v2.exceptions import OperationNotSupported
from minfx.neptune_v2.types.value_visitor import ValueVisitor

class ValueToAttributeVisitor(ValueVisitor[Attribute]):

    def __init__(self, container, path):
        self._container = container
        self._path = path

    def visit_float(self, _):
        return FloatAttr(self._container, self._path)

    def visit_integer(self, _):
        return IntegerAttr(self._container, self._path)

    def visit_boolean(self, _):
        return BooleanAttr(self._container, self._path)

    def visit_string(self, _):
        return StringAttr(self._container, self._path)

    def visit_datetime(self, _):
        return DatetimeAttr(self._container, self._path)

    def visit_artifact(self, _):
        return ArtifactAttr(self._container, self._path)

    def visit_file(self, _):
        return FileAttr(self._container, self._path)

    def visit_file_set(self, _):
        return FileSetAttr(self._container, self._path)

    def visit_float_series(self, _):
        return FloatSeriesAttr(self._container, self._path)

    def visit_string_series(self, _):
        return StringSeriesAttr(self._container, self._path)

    def visit_image_series(self, _):
        return ImageSeriesAttr(self._container, self._path)

    def visit_string_set(self, _):
        return StringSetAttr(self._container, self._path)

    def visit_git_ref(self, _):
        raise OperationNotSupported('Cannot create custom attribute of type GitRef')

    def visit_namespace(self, _):
        return NamespaceAttr(self._container, self._path)

    def copy_value(self, source_type, source_path):
        return source_type(self._container, self._path)