from __future__ import annotations
__all__ = ['get_artifact_attribute', 'list_artifact_files', 'track_to_existing_artifact', 'track_to_new_artifact']
from typing import TYPE_CHECKING
from bravado.exception import HTTPNotFound
from minfx.neptune_v2.common.backends.utils import with_api_exceptions_handler
from minfx.neptune_v2.exceptions import ArtifactNotFoundException, ArtifactUploadingError, FetchAttributeNotFoundException, NeptuneEmptyLocationException
from minfx.neptune_v2.internal.artifacts.file_hasher import FileHasher
from minfx.neptune_v2.internal.artifacts.types import ArtifactDriver, ArtifactDriversMap, ArtifactFileData
from minfx.neptune_v2.internal.backends.api_model import ArtifactAttribute, ArtifactModel
from minfx.neptune_v2.internal.operation import AssignArtifact, Operation
from minfx.neptune_v2.internal.utils.paths import path_to_str

def _compute_artifact_size(artifact_file_list):
    artifact_size = 0
    for artifact_file in artifact_file_list:
        if artifact_file.size is None:
            return None
        artifact_size += artifact_file.size
    return artifact_size

def _filter_empty_directory_files(files):
    return list(filter(lambda x: not _is_s3_empty_directory_file(x), files))

def _is_s3_empty_directory_file(file):
    return file.type == 'S3' and file.size == 0

def track_to_new_artifact(swagger_client, project_id, path, parent_identifier, entries, default_request_params, exclude_directory_files, exclude_metadata_from_hash):
    files = _extract_file_list(path, entries)
    if exclude_directory_files:
        files = _filter_empty_directory_files(files)
    if not files:
        raise ArtifactUploadingError('Uploading an empty Artifact')
    artifact_hash = _compute_artifact_hash_without_metadata(files) if exclude_metadata_from_hash else _compute_artifact_hash(files)
    artifact = create_new_artifact(swagger_client=swagger_client, project_id=project_id, artifact_hash=artifact_hash, parent_identifier=parent_identifier, size=_compute_artifact_size(files), default_request_params=default_request_params)
    if not artifact.received_metadata:
        upload_artifact_files_metadata(swagger_client=swagger_client, project_id=project_id, artifact_hash=artifact_hash, files=files, default_request_params=default_request_params)
    return AssignArtifact(path=path, hash=artifact_hash)

def track_to_existing_artifact(swagger_client, project_id, path, artifact_hash, parent_identifier, entries, default_request_params, exclude_directory_files):
    files = _extract_file_list(path, entries)
    if exclude_directory_files:
        files = _filter_empty_directory_files(files)
    if not files:
        raise ArtifactUploadingError('Uploading an empty Artifact')
    artifact = create_artifact_version(swagger_client=swagger_client, project_id=project_id, artifact_hash=artifact_hash, parent_identifier=parent_identifier, files=files, default_request_params=default_request_params)
    return AssignArtifact(path=path, hash=artifact.hash)

def _compute_artifact_hash_without_metadata(files):
    return FileHasher.get_artifact_hash_without_metadata(files)

def _compute_artifact_hash(files):
    return FileHasher.get_artifact_hash(files)

def _extract_file_list(path, entries):
    files = []
    for entry_path, entry_destination in entries:
        driver = ArtifactDriversMap.match_path(entry_path)
        artifact_files = driver.get_tracked_files(path=entry_path, destination=entry_destination)
        if len(artifact_files) == 0:
            raise NeptuneEmptyLocationException(location=entry_path, namespace='/'.join(path))
        files.extend(artifact_files)
    return files

@with_api_exceptions_handler
def create_new_artifact(swagger_client, project_id, artifact_hash, parent_identifier, size, default_request_params):
    params = {'projectIdentifier': project_id, 'hash': artifact_hash, 'size': size, 'parentIdentifier': parent_identifier, **add_artifact_version_to_request_params(default_request_params)}
    try:
        result = swagger_client.api.createNewArtifact(**params).response().result
        return ArtifactModel(hash=result.artifactHash, received_metadata=result.receivedMetadata, size=result.size)
    except HTTPNotFound:
        raise ArtifactNotFoundException(artifact_hash)

@with_api_exceptions_handler
def upload_artifact_files_metadata(swagger_client, project_id, artifact_hash, files, default_request_params):
    params = {'projectIdentifier': project_id, 'hash': artifact_hash, 'artifactFilesDTO': {'files': [ArtifactFileData.to_dto(a) for a in files]}, **add_artifact_version_to_request_params(default_request_params)}
    try:
        result = swagger_client.api.uploadArtifactFilesMetadata(**params).response().result
        return ArtifactModel(hash=result.artifactHash, size=result.size, received_metadata=result.receivedMetadata)
    except HTTPNotFound:
        raise ArtifactNotFoundException(artifact_hash)

@with_api_exceptions_handler
def create_artifact_version(swagger_client, project_id, artifact_hash, parent_identifier, files, default_request_params):
    params = {'projectIdentifier': project_id, 'hash': artifact_hash, 'parentIdentifier': parent_identifier, 'artifactFilesDTO': {'files': [ArtifactFileData.to_dto(a) for a in files]}, **add_artifact_version_to_request_params(default_request_params)}
    try:
        result = swagger_client.api.createArtifactVersion(**params).response().result
        return ArtifactModel(hash=result.artifactHash, size=result.size, received_metadata=result.receivedMetadata)
    except HTTPNotFound:
        raise ArtifactNotFoundException(artifact_hash)

@with_api_exceptions_handler
def get_artifact_attribute(swagger_client, parent_identifier, path, default_request_params):
    requests_params = add_artifact_version_to_request_params(default_request_params)
    params = {'experimentId': parent_identifier, 'attribute': path_to_str(path), **requests_params}
    try:
        result = swagger_client.api.getArtifactAttribute(**params).response().result
        return ArtifactAttribute(hash=result.hash)
    except HTTPNotFound:
        raise FetchAttributeNotFoundException(path_to_str(path))

@with_api_exceptions_handler
def list_artifact_files(swagger_client, project_id, artifact_hash, default_request_params):
    requests_params = add_artifact_version_to_request_params(default_request_params)
    params = {'projectIdentifier': project_id, 'hash': artifact_hash, **requests_params}
    try:
        result = swagger_client.api.listArtifactFiles(**params).response().result
        return [ArtifactFileData.from_dto(a) for a in result.files]
    except HTTPNotFound:
        raise ArtifactNotFoundException(artifact_hash)

def add_artifact_version_to_request_params(default_request_params):
    current_artifact_version = '2'
    return {'_request_options': {**default_request_params['_request_options'], 'headers': {**default_request_params['_request_options']['headers'], 'X-Neptune-Artifact-Api-Version': current_artifact_version}}}