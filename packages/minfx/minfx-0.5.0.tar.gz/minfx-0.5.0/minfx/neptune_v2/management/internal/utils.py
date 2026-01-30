from __future__ import annotations
from enum import Enum
import re
from minfx.neptune_v2.common.patterns import PROJECT_QUALIFIED_NAME_PATTERN
from minfx.neptune_v2.management.exceptions import ConflictingWorkspaceName, InvalidProjectName, MissingWorkspaceName

def extract_project_and_workspace(name, workspace=None):
    project_spec = re.search(PROJECT_QUALIFIED_NAME_PATTERN, name)
    if not project_spec:
        raise InvalidProjectName(name=name)
    extracted_workspace, extracted_project_name = (project_spec['workspace'], project_spec['project'])
    if not workspace and (not extracted_workspace):
        raise MissingWorkspaceName(name=name)
    if workspace and extracted_workspace and (workspace != extracted_workspace):
        raise ConflictingWorkspaceName(name=name, workspace=workspace)
    final_workspace_name = extracted_workspace or workspace
    return (final_workspace_name, extracted_project_name)

def normalize_project_name(name, workspace=None):
    extracted_workspace_name, extracted_project_name = extract_project_and_workspace(name=name, workspace=workspace)
    return f'{extracted_workspace_name}/{extracted_project_name}'

class WorkspaceMemberRole(Enum):
    MEMBER = 'member'
    ADMIN = 'admin'

    def to_api(self):
        if self.value == 'admin':
            return 'owner'
        return self.value