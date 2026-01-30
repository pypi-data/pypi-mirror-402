__all__ = ('MemberRole', 'ProjectMemberRole', 'ProjectVisibility', 'WorkspaceMemberRole')

class ProjectVisibility:
    PRIVATE = 'priv'
    PUBLIC = 'pub'
    WORKSPACE = 'workspace'

class ProjectMemberRole:
    VIEWER = 'viewer'
    OWNER = 'owner'
    CONTRIBUTOR = 'contributor'
    MEMBER = CONTRIBUTOR
    MANAGER = OWNER
MemberRole = ProjectMemberRole

class WorkspaceMemberRole:
    ADMIN = 'admin'
    MEMBER = 'member'