__all__ = ['OperationVisitor']
import abc
from typing import Generic, TypeVar
from minfx.neptune_v2.internal.operation import AddStrings, AssignArtifact, AssignBool, AssignDatetime, AssignFloat, AssignInt, AssignString, ClearArtifact, ClearFloatLog, ClearImageLog, ClearStringLog, ClearStringSet, ConfigFloatSeries, CopyAttribute, DeleteAttribute, DeleteFiles, LogFloats, LogImages, LogStrings, Operation, RemoveStrings, TrackFilesToArtifact, UploadFile, UploadFileContent, UploadFileSet
Ret = TypeVar('Ret')

class OperationVisitor(Generic[Ret]):

    def visit(self, op):
        return op.accept(self)

    @abc.abstractmethod
    def visit_assign_float(self, op):
        pass

    @abc.abstractmethod
    def visit_assign_int(self, op):
        pass

    @abc.abstractmethod
    def visit_assign_bool(self, op):
        pass

    @abc.abstractmethod
    def visit_assign_string(self, op):
        pass

    @abc.abstractmethod
    def visit_assign_datetime(self, op):
        pass

    @abc.abstractmethod
    def visit_assign_artifact(self, op):
        pass

    @abc.abstractmethod
    def visit_upload_file(self, op):
        pass

    @abc.abstractmethod
    def visit_upload_file_content(self, op):
        pass

    @abc.abstractmethod
    def visit_upload_file_set(self, op):
        pass

    @abc.abstractmethod
    def visit_log_floats(self, op):
        pass

    @abc.abstractmethod
    def visit_log_strings(self, op):
        pass

    @abc.abstractmethod
    def visit_log_images(self, op):
        pass

    @abc.abstractmethod
    def visit_clear_float_log(self, op):
        pass

    @abc.abstractmethod
    def visit_clear_string_log(self, op):
        pass

    @abc.abstractmethod
    def visit_clear_image_log(self, op):
        pass

    @abc.abstractmethod
    def visit_config_float_series(self, op):
        pass

    @abc.abstractmethod
    def visit_add_strings(self, op):
        pass

    @abc.abstractmethod
    def visit_remove_strings(self, op):
        pass

    @abc.abstractmethod
    def visit_delete_attribute(self, op):
        pass

    @abc.abstractmethod
    def visit_clear_string_set(self, op):
        pass

    @abc.abstractmethod
    def visit_delete_files(self, op):
        pass

    @abc.abstractmethod
    def visit_track_files_to_artifact(self, op):
        pass

    @abc.abstractmethod
    def visit_clear_artifact(self, op):
        pass

    @abc.abstractmethod
    def visit_copy_attribute(self, op):
        pass