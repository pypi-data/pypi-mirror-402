__all__ = ['OperationApiObjectConverter']
from minfx.neptune_v2.common.exceptions import InternalClientError
from minfx.neptune_v2.internal.operation import AddStrings, AssignArtifact, AssignBool, AssignDatetime, AssignFloat, AssignInt, AssignString, ClearArtifact, ClearFloatLog, ClearImageLog, ClearStringLog, ClearStringSet, ConfigFloatSeries, CopyAttribute, DeleteAttribute, DeleteFiles, LogFloats, LogImages, LogStrings, Operation, RemoveStrings, TrackFilesToArtifact, UploadFile, UploadFileContent, UploadFileSet
from minfx.neptune_v2.internal.operation_visitor import OperationVisitor, Ret

class OperationApiObjectConverter(OperationVisitor[dict]):

    def convert(self, op):
        return op.accept(self)

    def visit_assign_float(self, op):
        return {'value': op.value}

    def visit_assign_int(self, op):
        return {'value': op.value}

    def visit_assign_bool(self, op):
        return {'value': op.value}

    def visit_assign_string(self, op):
        return {'value': op.value}

    def visit_assign_datetime(self, op):
        return {'valueMilliseconds': int(1000 * op.value.timestamp())}

    def visit_assign_artifact(self, op):
        return {'hash': op.hash}

    def visit_upload_file(self, _):
        raise InternalClientError('Specialized endpoint should be used to upload file attribute')

    def visit_upload_file_content(self, _):
        raise InternalClientError('Specialized endpoint should be used to upload file attribute')

    def visit_upload_file_set(self, op):
        raise InternalClientError('Specialized endpoints should be used to upload file set attribute')

    def visit_log_floats(self, op):
        return {'entries': [{'value': value.value, 'step': value.step, 'timestampMilliseconds': int(value.ts * 1000)} for value in op.values]}

    def visit_log_strings(self, op):
        return {'entries': [{'value': value.value, 'step': value.step, 'timestampMilliseconds': int(value.ts * 1000)} for value in op.values]}

    def visit_log_images(self, op):
        return {'entries': [{'value': {'data': value.value.data, 'name': value.value.name, 'description': value.value.description}, 'step': value.step, 'timestampMilliseconds': int(value.ts * 1000)} for value in op.values]}

    def visit_clear_float_log(self, _):
        return {}

    def visit_clear_string_log(self, _):
        return {}

    def visit_clear_image_log(self, _):
        return {}

    def visit_config_float_series(self, op):
        return {'min': op.min, 'max': op.max, 'unit': op.unit}

    def visit_add_strings(self, op):
        return {'values': list(op.values)}

    def visit_remove_strings(self, op):
        return {'values': list(op.values)}

    def visit_delete_attribute(self, _):
        return {}

    def visit_clear_string_set(self, _):
        return {}

    def visit_delete_files(self, op):
        return {'filePaths': list(op.file_paths)}

    def visit_track_files_to_artifact(self, op):
        raise InternalClientError('Specialized endpoint should be used to track artifact files')

    def visit_clear_artifact(self, _):
        return {}

    def visit_copy_attribute(self, _):
        raise NotImplementedError('This operation is client-side only')