from __future__ import annotations
__all__ = ['WorkspaceMemberRole', 'add_project_member', 'add_project_service_account', 'clear_trash', 'create_project', 'delete_objects_from_trash', 'delete_project', 'get_project_list', 'get_project_member_list', 'get_project_service_account_list', 'get_workspace_member_list', 'get_workspace_service_account_list', 'get_workspace_status', 'invite_to_workspace', 'remove_project_member', 'remove_project_service_account', 'trash_objects']
import os
from typing import TYPE_CHECKING, Any, Iterable
from bravado.exception import HTTPBadRequest, HTTPConflict, HTTPForbidden, HTTPNotFound, HTTPUnprocessableEntity
from minfx.neptune_v2.common.backends.utils import with_api_exceptions_handler
from minfx.neptune_v2.common.envs import API_TOKEN_ENV_NAME
from minfx.neptune_v2.internal.backends.hosted_client import DEFAULT_REQUEST_KWARGS, create_backend_client, create_http_client_with_auth, create_leaderboard_client
from minfx.neptune_v2.internal.backends.utils import parse_validation_errors, ssl_verify
from minfx.neptune_v2.internal.credentials import Credentials
from minfx.neptune_v2.internal.id_formats import QualifiedName
from minfx.neptune_v2.internal.utils import verify_collection_type, verify_type
from minfx.neptune_v2.internal.utils.iteration import get_batches
from minfx.neptune_v2.internal.utils.logger import get_logger
from minfx.neptune_v2.management.exceptions import AccessRevokedOnDeletion, AccessRevokedOnMemberRemoval, AccessRevokedOnServiceAccountRemoval, BadRequestException, ProjectAlreadyExists, ProjectNotFound, ServiceAccountAlreadyHasAccess, ServiceAccountNotExistsOrWithoutAccess, ServiceAccountNotFound, UserAlreadyHasAccess, UserAlreadyInvited, UserNotExistsOrWithoutAccess, WorkspaceNotFound, WorkspaceOrUserNotFound
from minfx.neptune_v2.management.internal.dto import ProjectMemberRoleDTO, ProjectVisibilityDTO, ServiceAccountDTO, WorkspaceMemberRoleDTO
from minfx.neptune_v2.management.internal.types import ProjectVisibility
from minfx.neptune_v2.management.internal.utils import WorkspaceMemberRole, extract_project_and_workspace, normalize_project_name
logger = get_logger()
TRASH_BATCH_SIZE = 100

def _get_token(api_token=None):
    return api_token or os.getenv(API_TOKEN_ENV_NAME)

def _get_http_client_and_api_url(api_token=None):
    credentials = Credentials.from_token(api_token=_get_token(api_token=api_token))
    http_client, _client_config, api_url = create_http_client_with_auth(credentials=credentials, ssl_verify=ssl_verify(), proxies={})
    return (http_client, api_url)

def _get_backend_client(api_token=None):
    http_client, api_url = _get_http_client_and_api_url(api_token)
    return create_backend_client(api_url=api_url, http_client=http_client)

def _get_leaderboard_client(api_token=None):
    http_client, api_url = _get_http_client_and_api_url(api_token)
    return create_leaderboard_client(api_url=api_url, http_client=http_client)

def get_project_list(*, api_token=None):
    verify_type('api_token', api_token, (str, type(None)))
    backend_client = _get_backend_client(api_token=api_token)
    params = {'userRelation': 'viewerOrHigher', 'sortBy': ['lastViewed'], **DEFAULT_REQUEST_KWARGS}
    projects = _get_projects(backend_client, params)
    return [normalize_project_name(name=project.name, workspace=project.organizationName) for project in projects]

@with_api_exceptions_handler
def _get_projects(backend_client, params):
    return backend_client.api.listProjects(**params).response().result.entries

def create_project(name, *, key=None, workspace=None, visibility=ProjectVisibility.PRIVATE, description=None, api_token=None):
    verify_type('name', name, str)
    verify_type('key', key, (str, type(None)))
    verify_type('workspace', workspace, (str, type(None)))
    verify_type('visibility', visibility, str)
    verify_type('description', description, (str, type(None)))
    verify_type('api_token', api_token, (str, type(None)))
    backend_client = _get_backend_client(api_token=api_token)
    workspace, name = extract_project_and_workspace(name=name, workspace=workspace)
    project_qualified_name = f'{workspace}/{name}'
    workspace_id = _get_workspace_id(backend_client, workspace)
    params = {'projectToCreate': {'name': name, 'description': description, 'projectKey': key, 'organizationId': workspace_id, 'visibility': ProjectVisibilityDTO.from_str(visibility).value}, **DEFAULT_REQUEST_KWARGS}
    project_response = _create_project(backend_client, project_qualified_name, params)
    return normalize_project_name(name=project_response.result.name, workspace=project_response.result.organizationName)

def _get_workspace_id(backend_client, workspace):
    workspaces = _get_workspaces(backend_client)
    workspace_name_to_id = {f'{f.name}': f.id for f in workspaces}
    if workspace not in workspace_name_to_id:
        raise WorkspaceNotFound(workspace=workspace)
    return workspace_name_to_id[workspace]

@with_api_exceptions_handler
def _get_workspaces(backend_client):
    return backend_client.api.listOrganizations(**DEFAULT_REQUEST_KWARGS).response().result

@with_api_exceptions_handler
def _create_project(backend_client, project_qualified_name, params):
    try:
        return backend_client.api.createProject(**params).response()
    except HTTPBadRequest as e:
        validation_errors = parse_validation_errors(error=e)
        if 'ERR_NOT_UNIQUE' in validation_errors:
            raise ProjectAlreadyExists(name=project_qualified_name) from e
        raise BadRequestException(validation_errors=validation_errors)

@with_api_exceptions_handler
def delete_project(project, *, workspace=None, api_token=None):
    verify_type('project', project, str)
    verify_type('workspace', workspace, (str, type(None)))
    verify_type('api_token', api_token, (str, type(None)))
    backend_client = _get_backend_client(api_token=api_token)
    project_identifier = normalize_project_name(name=project, workspace=workspace)
    params = {'projectIdentifier': project_identifier, **DEFAULT_REQUEST_KWARGS}
    try:
        backend_client.api.deleteProject(**params).response()
    except HTTPNotFound as e:
        raise ProjectNotFound(name=project_identifier) from e
    except HTTPForbidden as e:
        raise AccessRevokedOnDeletion(name=project_identifier) from e

@with_api_exceptions_handler
def add_project_member(project, username, role, *, workspace=None, api_token=None):
    verify_type('project', project, str)
    verify_type('username', username, str)
    verify_type('role', role, str)
    verify_type('workspace', workspace, (str, type(None)))
    verify_type('api_token', api_token, (str, type(None)))
    backend_client = _get_backend_client(api_token=api_token)
    project_identifier = normalize_project_name(name=project, workspace=workspace)
    params = {'projectIdentifier': project_identifier, 'member': {'userId': username, 'role': ProjectMemberRoleDTO.from_str(role).value}, **DEFAULT_REQUEST_KWARGS}
    try:
        backend_client.api.addProjectMember(**params).response()
    except HTTPNotFound as e:
        raise ProjectNotFound(name=project_identifier) from e
    except HTTPConflict as e:
        members = get_project_member_list(project=project, workspace=workspace, api_token=api_token)
        user_role = members.get(username)
        raise UserAlreadyHasAccess(user=username, project=project_identifier, role=user_role) from e

@with_api_exceptions_handler
def get_project_member_list(project, *, workspace=None, api_token=None):
    verify_type('project', project, str)
    verify_type('workspace', workspace, (str, type(None)))
    verify_type('api_token', api_token, (str, type(None)))
    backend_client = _get_backend_client(api_token=api_token)
    project_identifier = normalize_project_name(name=project, workspace=workspace)
    params = {'projectIdentifier': project_identifier, **DEFAULT_REQUEST_KWARGS}
    try:
        result = backend_client.api.listProjectMembers(**params).response().result
        return {f'{m.registeredMemberInfo.username}': ProjectMemberRoleDTO.to_domain(m.role) for m in result if m.registeredMemberInfo is not None}
    except HTTPNotFound as e:
        raise ProjectNotFound(name=project_identifier) from e

@with_api_exceptions_handler
def remove_project_member(project, username, *, workspace=None, api_token=None):
    verify_type('project', project, str)
    verify_type('username', username, str)
    verify_type('workspace', workspace, (str, type(None)))
    verify_type('api_token', api_token, (str, type(None)))
    backend_client = _get_backend_client(api_token=api_token)
    project_identifier = normalize_project_name(name=project, workspace=workspace)
    params = {'projectIdentifier': project_identifier, 'userId': username, **DEFAULT_REQUEST_KWARGS}
    try:
        backend_client.api.deleteProjectMember(**params).response()
    except HTTPNotFound as e:
        raise ProjectNotFound(name=project_identifier) from e
    except HTTPUnprocessableEntity as e:
        raise UserNotExistsOrWithoutAccess(user=username, project=project_identifier) from e
    except HTTPForbidden as e:
        raise AccessRevokedOnMemberRemoval(user=username, project=project_identifier) from e

@with_api_exceptions_handler
def get_workspace_member_list(workspace, *, api_token=None):
    verify_type('workspace', workspace, str)
    verify_type('api_token', api_token, (str, type(None)))
    backend_client = _get_backend_client(api_token=api_token)
    params = {'organizationIdentifier': workspace, **DEFAULT_REQUEST_KWARGS}
    try:
        result = backend_client.api.listOrganizationMembers(**params).response().result
        return {f'{m.registeredMemberInfo.username}': WorkspaceMemberRoleDTO.to_domain(m.role) for m in result if m.registeredMemberInfo is not None}
    except HTTPNotFound as e:
        raise WorkspaceNotFound(workspace=workspace) from e

@with_api_exceptions_handler
def _get_raw_workspace_service_account_list(workspace_name, api_token=None):
    verify_type('workspace_name', workspace_name, str)
    verify_type('api_token', api_token, (str, type(None)))
    backend_client = _get_backend_client(api_token=api_token)
    params = {'organizationIdentifier': workspace_name, 'deactivated': False, **DEFAULT_REQUEST_KWARGS}
    try:
        result = backend_client.api.listServiceAccounts(**params).response().result
        return {f'{sa.displayName}': ServiceAccountDTO(name=sa.displayName, id=sa.id) for sa in result}
    except HTTPNotFound as e:
        raise WorkspaceNotFound(workspace=workspace_name) from e

@with_api_exceptions_handler
def get_workspace_service_account_list(workspace, *, api_token=None):
    service_accounts = _get_raw_workspace_service_account_list(workspace_name=workspace, api_token=api_token)
    return {service_account_name: WorkspaceMemberRoleDTO.to_domain('member') for service_account_name, _ in service_accounts.items()}

@with_api_exceptions_handler
def invite_to_workspace(*, username=None, email=None, workspace, api_token=None, role=WorkspaceMemberRole.MEMBER, add_to_all_projects=False):
    verify_type('workspace', workspace, str)
    verify_type('role', role, (WorkspaceMemberRole, str))
    verify_type('add_to_all_projects', add_to_all_projects, bool)
    verify_type('username', username, (str, type(None)))
    verify_type('email', email, (str, type(None)))
    verify_type('api_token', api_token, (str, type(None)))
    if username and email:
        raise ValueError('Cannot specify both `username` and `email`.')
    if username:
        invitee = username
        invitation_type = 'user'
    elif email:
        invitee = email
        invitation_type = 'emailRecipient'
    else:
        raise ValueError('Neither `username` nor `email` arguments filled. At least one needs to be passed')
    if isinstance(role, str):
        role = WorkspaceMemberRole(role)
    params = {'newOrganizationInvitations': {'invitationsEntries': [{'invitee': invitee, 'invitationType': invitation_type, 'roleGrant': role.to_api(), 'addToAllProjects': add_to_all_projects}], 'organizationIdentifier': workspace}, **DEFAULT_REQUEST_KWARGS}
    backend_client = _get_backend_client(api_token=api_token)
    try:
        backend_client.api.createOrganizationInvitations(**params)
    except HTTPNotFound:
        raise WorkspaceOrUserNotFound(workspace=workspace, user=invitee)
    except HTTPConflict:
        raise UserAlreadyInvited(user=invitee, workspace=workspace)

@with_api_exceptions_handler
def get_project_service_account_list(project, *, workspace=None, api_token=None):
    verify_type('project', project, str)
    verify_type('workspace', workspace, (str, type(None)))
    verify_type('api_token', api_token, (str, type(None)))
    backend_client = _get_backend_client(api_token=api_token)
    project_identifier = normalize_project_name(name=project, workspace=workspace)
    params = {'projectIdentifier': project_identifier, **DEFAULT_REQUEST_KWARGS}
    try:
        result = backend_client.api.listProjectServiceAccounts(**params).response().result
        return {f'{sa.serviceAccountInfo.displayName}': ProjectMemberRoleDTO.to_domain(sa.role) for sa in result}
    except HTTPNotFound as e:
        raise ProjectNotFound(name=project_identifier) from e

@with_api_exceptions_handler
def add_project_service_account(project, service_account_name, role, *, workspace=None, api_token=None):
    verify_type('project', project, str)
    verify_type('service_account_name', service_account_name, str)
    verify_type('role', role, str)
    verify_type('workspace', workspace, (str, type(None)))
    verify_type('api_token', api_token, (str, type(None)))
    backend_client = _get_backend_client(api_token=api_token)
    workspace, project_name = extract_project_and_workspace(name=project, workspace=workspace)
    project_qualified_name = f'{workspace}/{project_name}'
    try:
        service_account = _get_raw_workspace_service_account_list(workspace_name=workspace, api_token=api_token)[service_account_name]
    except KeyError as e:
        raise ServiceAccountNotFound(service_account_name=service_account_name, workspace=workspace) from e
    params = {'projectIdentifier': project_qualified_name, 'account': {'serviceAccountId': service_account.id, 'role': ProjectMemberRoleDTO.from_str(role).value}, **DEFAULT_REQUEST_KWARGS}
    try:
        backend_client.api.addProjectServiceAccount(**params).response()
    except HTTPNotFound as e:
        raise ProjectNotFound(name=project_qualified_name) from e
    except HTTPConflict as e:
        service_accounts = get_project_service_account_list(project=project, workspace=workspace, api_token=api_token)
        service_account_role = service_accounts.get(service_account_name)
        raise ServiceAccountAlreadyHasAccess(service_account_name=service_account_name, project=project_qualified_name, role=service_account_role) from e

@with_api_exceptions_handler
def remove_project_service_account(project, service_account_name, *, workspace=None, api_token=None):
    verify_type('project', project, str)
    verify_type('service_account_name', service_account_name, str)
    verify_type('workspace', workspace, (str, type(None)))
    verify_type('api_token', api_token, (str, type(None)))
    backend_client = _get_backend_client(api_token=api_token)
    workspace, project_name = extract_project_and_workspace(name=project, workspace=workspace)
    project_qualified_name = f'{workspace}/{project_name}'
    try:
        service_account = _get_raw_workspace_service_account_list(workspace_name=workspace, api_token=api_token)[service_account_name]
    except KeyError as e:
        raise ServiceAccountNotFound(service_account_name=service_account_name, workspace=workspace) from e
    params = {'projectIdentifier': project_qualified_name, 'serviceAccountId': service_account.id, **DEFAULT_REQUEST_KWARGS}
    try:
        backend_client.api.deleteProjectServiceAccount(**params).response()
    except HTTPNotFound as e:
        raise ProjectNotFound(name=project_qualified_name) from e
    except HTTPUnprocessableEntity as e:
        raise ServiceAccountNotExistsOrWithoutAccess(service_account_name=service_account_name, project=project_qualified_name) from e
    except HTTPForbidden as e:
        raise AccessRevokedOnServiceAccountRemoval(service_account_name=service_account_name, project=project_qualified_name) from e

def trash_objects(project, ids, *, workspace=None, api_token=None):
    verify_type('project', project, str)
    verify_type('workspace', workspace, (str, type(None)))
    verify_type('api_token', api_token, (str, type(None)))
    if ids is not None:
        if isinstance(ids, str):
            ids = [ids]
        else:
            verify_collection_type('ids', ids, str)
    leaderboard_client = _get_leaderboard_client(api_token=api_token)
    workspace, project_name = extract_project_and_workspace(name=project, workspace=workspace)
    project_qualified_name = f'{workspace}/{project_name}'
    qualified_name_ids = [QualifiedName(f'{workspace}/{project_name}/{container_id}') for container_id in ids]
    errors = []
    succeeded = 0
    for batch_ids in get_batches(qualified_name_ids, batch_size=TRASH_BATCH_SIZE):
        params = {'projectIdentifier': project_qualified_name, 'experimentIdentifiers': batch_ids, **DEFAULT_REQUEST_KWARGS}
        try:
            response = leaderboard_client.api.trashExperiments(**params).response()
        except HTTPNotFound as e:
            raise ProjectNotFound(name=project_qualified_name) from e
        errors += response.result.errors
        succeeded += len(response.result.updatedExperimentIdentifiers)
    for error in errors:
        logger.warning(error)
    logger.info('Successfully trashed objects: %d. Number of failures: %d.', succeeded, len(ids) - succeeded)

def delete_objects_from_trash(project, ids, *, workspace=None, api_token=None):
    verify_type('project', project, str)
    verify_type('workspace', workspace, (str, type(None)))
    verify_type('api_token', api_token, (str, type(None)))
    workspace, project_name = extract_project_and_workspace(name=project, workspace=workspace)
    project_qualified_name = f'{workspace}/{project_name}'
    if isinstance(ids, str):
        ids = [ids]
    verify_collection_type('ids', ids, str)
    leaderboard_client = _get_leaderboard_client(api_token=api_token)
    qualified_name_ids = [QualifiedName(f'{workspace}/{project_name}/{container_id}') for container_id in ids]
    for batch_ids in get_batches(qualified_name_ids, batch_size=TRASH_BATCH_SIZE):
        params = {'projectIdentifier': project_qualified_name, 'experimentIdentifiers': batch_ids, **DEFAULT_REQUEST_KWARGS}
        response = leaderboard_client.api.deleteExperiments(**params).response()
        for error in response.result.errors:
            logger.warning(error)

def clear_trash(project, *, workspace=None, api_token=None):
    verify_type('project', project, str)
    verify_type('workspace', workspace, (str, type(None)))
    verify_type('api_token', api_token, (str, type(None)))
    leaderboard_client = _get_leaderboard_client(api_token=api_token)
    workspace, project_name = extract_project_and_workspace(name=project, workspace=workspace)
    project_qualified_name = f'{workspace}/{project_name}'
    params = {'projectIdentifier': project_qualified_name, **DEFAULT_REQUEST_KWARGS}
    response = leaderboard_client.api.deleteAllExperiments(**params).response()
    for error in response.result.errors:
        logger.warning(error)

def get_workspace_status(workspace, *, api_token=None):
    verify_type('workspace', workspace, str)
    verify_type('api_token', api_token, (str, type(None)))
    backend_client = _get_backend_client(api_token=api_token)
    params = {'organizationIdentifier': workspace, **DEFAULT_REQUEST_KWARGS}
    try:
        response = backend_client.api.workspaceStatus(**params).response()
        result = {}
        if hasattr(response.result, 'storageBytesAvailable'):
            result['storageBytesAvailable'] = response.result.storageBytesAvailable
        if hasattr(response.result, 'storageBytesLimit'):
            result['storageBytesLimit'] = response.result.storageBytesLimit
        if hasattr(response.result, 'storageBytesAvailable') and hasattr(response.result, 'storageBytesLimit'):
            result['storageBytesUsed'] = response.result.storageBytesLimit - response.result.storageBytesAvailable
        if hasattr(response.result, 'activeProjectsUsage'):
            result['activeProjectsUsage'] = response.result.activeProjectsUsage
        if hasattr(response.result, 'activeProjectsLimit'):
            result['activeProjectsLimit'] = response.result.activeProjectsLimit
        if hasattr(response.result, 'membersCount'):
            result['membersCount'] = response.result.membersCount
        return result
    except HTTPNotFound as e:
        raise WorkspaceNotFound(workspace=workspace) from e