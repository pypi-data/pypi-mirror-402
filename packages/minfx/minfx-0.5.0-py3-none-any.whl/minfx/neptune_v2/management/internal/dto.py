from dataclasses import dataclass
from enum import Enum
from minfx.neptune_v2.internal.utils import verify_type
from minfx.neptune_v2.management.exceptions import UnsupportedValue
from minfx.neptune_v2.management.internal.types import ProjectMemberRole, ProjectVisibility, WorkspaceMemberRole

class ProjectVisibilityDTO(Enum):
    PRIVATE = 'priv'
    PUBLIC = 'pub'
    WORKSPACE = 'workspace'

    @classmethod
    def from_str(cls, visibility):
        verify_type('visibility', visibility, str)
        try:
            return {ProjectVisibility.PRIVATE: ProjectVisibilityDTO.PRIVATE, ProjectVisibility.PUBLIC: ProjectVisibilityDTO.PUBLIC, ProjectVisibility.WORKSPACE: ProjectVisibilityDTO.WORKSPACE}[visibility]
        except KeyError as e:
            raise UnsupportedValue(enum=cls.__name__, value=visibility) from e

class ProjectMemberRoleDTO(Enum):
    VIEWER = 'viewer'
    MEMBER = 'member'
    MANAGER = 'manager'

    @classmethod
    def from_str(cls, role):
        verify_type('role', role, str)
        try:
            return {ProjectMemberRole.VIEWER: ProjectMemberRoleDTO.VIEWER, ProjectMemberRole.CONTRIBUTOR: ProjectMemberRoleDTO.MEMBER, ProjectMemberRole.OWNER: ProjectMemberRoleDTO.MANAGER}[role]
        except KeyError as e:
            raise UnsupportedValue(enum=cls.__name__, value=role) from e

    @staticmethod
    def to_domain(role):
        verify_type('role', role, str)
        return {ProjectMemberRoleDTO.VIEWER.value: ProjectMemberRole.VIEWER, ProjectMemberRoleDTO.MANAGER.value: ProjectMemberRole.OWNER, ProjectMemberRoleDTO.MEMBER.value: ProjectMemberRole.CONTRIBUTOR}.get(role)

class WorkspaceMemberRoleDTO(Enum):
    OWNER = 'owner'
    MEMBER = 'member'

    @staticmethod
    def to_domain(role):
        return {WorkspaceMemberRoleDTO.OWNER.value: WorkspaceMemberRole.ADMIN, WorkspaceMemberRoleDTO.MEMBER.value: WorkspaceMemberRole.MEMBER}.get(role)

@dataclass
class ServiceAccountDTO:
    name: str
    id: str