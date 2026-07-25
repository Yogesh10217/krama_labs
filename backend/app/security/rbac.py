from enum import Enum
from typing import List, Dict

class Permission(str, Enum):
    DOCUMENTS_READ = "documents.read"
    DOCUMENTS_WRITE = "documents.write"
    JOBS_READ = "jobs.read"
    JOBS_EXECUTE = "jobs.execute"
    JOBS_CANCEL = "jobs.cancel"
    REVIEW_READ = "review.read"
    REVIEW_APPROVE = "review.approve"
    PROVIDERS_MANAGE = "providers.manage"
    USERS_MANAGE = "users.manage"
    ADMIN_ALL = "admin.all"

# Role to Permissions matrix
ROLE_PERMISSIONS: Dict[str, List[Permission]] = {
    "SYSTEM_ADMIN": [Permission.ADMIN_ALL],
    "OWNER": [
        Permission.DOCUMENTS_READ, Permission.DOCUMENTS_WRITE,
        Permission.JOBS_READ, Permission.JOBS_EXECUTE, Permission.JOBS_CANCEL,
        Permission.REVIEW_READ, Permission.REVIEW_APPROVE,
        Permission.PROVIDERS_MANAGE, Permission.USERS_MANAGE
    ],
    "ADMIN": [
        Permission.DOCUMENTS_READ, Permission.DOCUMENTS_WRITE,
        Permission.JOBS_READ, Permission.JOBS_EXECUTE, Permission.JOBS_CANCEL,
        Permission.REVIEW_READ, Permission.REVIEW_APPROVE,
        Permission.USERS_MANAGE
    ],
    "REVIEWER": [
        Permission.DOCUMENTS_READ,
        Permission.JOBS_READ,
        Permission.REVIEW_READ, Permission.REVIEW_APPROVE
    ],
    "OPERATOR": [
        Permission.DOCUMENTS_READ, Permission.DOCUMENTS_WRITE,
        Permission.JOBS_READ, Permission.JOBS_EXECUTE, Permission.JOBS_CANCEL,
        Permission.REVIEW_READ
    ],
    "VIEWER": [
        Permission.DOCUMENTS_READ,
        Permission.JOBS_READ,
        Permission.REVIEW_READ
    ],
    "API_CLIENT": [] # Scopes are explicitly defined on the API Key
}

def has_permission(role: str, permission: Permission, scopes: List[str] = None) -> bool:
    """
    Evaluates if a role has the requested permission.
    For API_CLIENT, evaluates against provided scopes.
    """
    if role == "SYSTEM_ADMIN":
        return True
        
    if role == "API_CLIENT":
        if not scopes:
            return False
        return "*" in scopes or permission.value in scopes
        
    role_perms = ROLE_PERMISSIONS.get(role, [])
    return Permission.ADMIN_ALL in role_perms or permission in role_perms
