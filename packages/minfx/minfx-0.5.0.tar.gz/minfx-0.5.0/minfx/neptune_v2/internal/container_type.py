__all__ = ['ContainerType']
import enum
from minfx.neptune_v2.internal.id_formats import UniqueId

class ContainerType(str, enum.Enum):
    RUN = 'run'
    PROJECT = 'project'
    MODEL = 'model'
    MODEL_VERSION = 'model_version'

    def to_api(self):
        if self == ContainerType.MODEL_VERSION:
            return 'modelVersion'
        return self.value

    @staticmethod
    def from_api(api_type):
        if api_type == 'modelVersion':
            return ContainerType.MODEL_VERSION
        return ContainerType(api_type)

    def create_dir_name(self, container_id):
        return f'{self.value}__{container_id}'