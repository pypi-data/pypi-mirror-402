__all__ = ['OperationApiNameVisitor']
from minfx.neptune_v2.common.exceptions import InternalClientError
from minfx.neptune_v2.internal.operation import AddStrings, AssignArtifact, AssignBool, AssignDatetime, AssignFloat, AssignInt, AssignString, ClearArtifact, ClearFloatLog, ClearImageLog, ClearStringLog, ClearStringSet, ConfigFloatSeries, CopyAttribute, DeleteAttribute, DeleteFiles, LogFloats, LogImages, LogStrings, Operation, RemoveStrings, TrackFilesToArtifact, UploadFile, UploadFileContent, UploadFileSet
from minfx.neptune_v2.internal.operation_visitor import OperationVisitor, Ret

class OperationApiNameVisitor(OperationVisitor[str]):

    def visit(self, op):
        return op.accept(self)

    def visit_assign_float(self, _):
        return 'assignFloat'

    def visit_assign_int(self, _):
        return 'assignInt'

    def visit_assign_bool(self, _):
        return 'assignBool'

    def visit_assign_string(self, _):
        return 'assignString'

    def visit_assign_datetime(self, _):
        return 'assignDatetime'

    def visit_upload_file(self, _):
        raise InternalClientError('Specialized endpoint should be used to upload file attribute')

    def visit_upload_file_content(self, _):
        raise InternalClientError('Specialized endpoint should be used to upload file attribute')

    def visit_upload_file_set(self, op):
        raise InternalClientError('Specialized endpoints should be used to upload file set attribute')

    def visit_log_floats(self, _):
        return 'logFloats'

    def visit_log_strings(self, _):
        return 'logStrings'

    def visit_log_images(self, _):
        return 'logImages'

    def visit_clear_float_log(self, _):
        return 'clearFloatSeries'

    def visit_clear_string_log(self, _):
        return 'clearStringSeries'

    def visit_clear_image_log(self, _):
        return 'clearImageSeries'

    def visit_config_float_series(self, _):
        return 'configFloatSeries'

    def visit_add_strings(self, _):
        return 'insertStrings'

    def visit_remove_strings(self, _):
        return 'removeStrings'

    def visit_delete_attribute(self, _):
        return 'deleteAttribute'

    def visit_clear_string_set(self, _):
        return 'clearStringSet'

    def visit_delete_files(self, _):
        return 'deleteFiles'

    def visit_assign_artifact(self, _):
        return 'assignArtifact'

    def visit_track_files_to_artifact(self, _):
        raise InternalClientError('Specialized endpoint should be used to track artifact files')

    def visit_clear_artifact(self, _):
        return 'clearArtifact'

    def visit_copy_attribute(self, _):
        raise NotImplementedError('This operation is client-side only')