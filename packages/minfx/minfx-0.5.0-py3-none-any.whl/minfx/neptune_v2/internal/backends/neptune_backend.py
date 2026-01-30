from __future__ import annotations
__all__ = ['NeptuneBackend']
import abc
from typing import TYPE_CHECKING, Any, Generator

class NeptuneBackend:

    def close(self):
        pass

    @abc.abstractmethod
    def get_display_address(self):
        pass

    def verify_feature_available(self, _):
        pass

    def websockets_factory(self, project_id, run_id):
        return None

    @abc.abstractmethod
    def get_project(self, project_id):
        pass

    @abc.abstractmethod
    def get_available_projects(self, workspace_id=None, search_term=None):
        pass

    @abc.abstractmethod
    def get_available_workspaces(self):
        pass

    @abc.abstractmethod
    def create_run(self, project_id, git_info=None, custom_run_id=None, notebook_id=None, checkpoint_id=None, *, _external_id=None, _external_sys_id=None):
        pass

    @abc.abstractmethod
    def create_model(self, project_id, key):
        pass

    @abc.abstractmethod
    def create_model_version(self, project_id, model_id):
        pass

    @abc.abstractmethod
    def get_metadata_container(self, container_id, expected_container_type):
        pass

    @abc.abstractmethod
    def create_checkpoint(self, notebook_id, jupyter_path):
        pass

    def ping(self, container_id, container_type):
        pass

    def health_ping(self):
        pass

    @abc.abstractmethod
    def execute_operations(self, container_id, container_type, operations, operation_storage):
        pass

    @abc.abstractmethod
    def get_attributes(self, container_id, container_type):
        pass

    @abc.abstractmethod
    def download_file(self, container_id, container_type, path, destination=None, progress_bar=None):
        pass

    @abc.abstractmethod
    def download_file_set(self, container_id, container_type, path, destination=None, progress_bar=None):
        pass

    @abc.abstractmethod
    def get_float_attribute(self, container_id, container_type, path):
        pass

    @abc.abstractmethod
    def get_int_attribute(self, container_id, container_type, path):
        pass

    @abc.abstractmethod
    def get_bool_attribute(self, container_id, container_type, path):
        pass

    @abc.abstractmethod
    def get_file_attribute(self, container_id, container_type, path):
        pass

    @abc.abstractmethod
    def get_string_attribute(self, container_id, container_type, path):
        pass

    @abc.abstractmethod
    def get_datetime_attribute(self, container_id, container_type, path):
        pass

    @abc.abstractmethod
    def get_artifact_attribute(self, container_id, container_type, path):
        pass

    @abc.abstractmethod
    def list_artifact_files(self, project_id, artifact_hash):
        pass

    @abc.abstractmethod
    def get_float_series_attribute(self, container_id, container_type, path):
        pass

    @abc.abstractmethod
    def get_string_series_attribute(self, container_id, container_type, path):
        pass

    @abc.abstractmethod
    def get_string_set_attribute(self, container_id, container_type, path):
        pass

    @abc.abstractmethod
    def download_file_series_by_index(self, container_id, container_type, path, index, destination, progress_bar):
        pass

    @abc.abstractmethod
    def get_image_series_values(self, container_id, container_type, path, offset, limit):
        pass

    @abc.abstractmethod
    def get_string_series_values(self, container_id, container_type, path, offset, limit):
        pass

    @abc.abstractmethod
    def get_float_series_values(self, container_id, container_type, path, offset, limit):
        pass

    @abc.abstractmethod
    def get_run_url(self, run_id, workspace, project_name, sys_id):
        pass

    @abc.abstractmethod
    def get_project_url(self, project_id, workspace, project_name):
        pass

    @abc.abstractmethod
    def get_model_url(self, model_id, workspace, project_name, sys_id):
        pass

    @abc.abstractmethod
    def get_model_version_url(self, model_version_id, model_id, workspace, project_name, sys_id):
        pass

    @abc.abstractmethod
    def fetch_atom_attribute_values(self, container_id, container_type, path):
        pass

    @abc.abstractmethod
    def search_leaderboard_entries(self, project_id, types=None, query=None, columns=None, limit=None, sort_by='sys/creation_time', ascending=False, progress_bar=None):
        pass

    @abc.abstractmethod
    def list_fileset_files(self, attribute, container_id, path):
        pass