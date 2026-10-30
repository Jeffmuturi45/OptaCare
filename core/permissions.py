from rest_framework.permissions import BasePermission

ROLE_HIERARCHY = [
    'super_admin', 'branch_admin', 'doctor',
    'nurse', 'receptionist', 'lab_tech', 'pharmacist',
]


def has_role(user, *roles):
    return user.is_authenticated and user.role in roles


class IsSuperAdmin(BasePermission):
    def has_permission(self, request, view):
        return has_role(request.user, 'super_admin')


class IsBranchAdmin(BasePermission):
    def has_permission(self, request, view):
        return has_role(request.user, 'super_admin', 'branch_admin')


class IsDoctor(BasePermission):
    def has_permission(self, request, view):
        return has_role(request.user, 'super_admin', 'doctor')


class IsNurse(BasePermission):
    def has_permission(self, request, view):
        return has_role(request.user, 'super_admin', 'nurse')


class IsReceptionist(BasePermission):
    def has_permission(self, request, view):
        return has_role(request.user, 'super_admin',
                        'branch_admin', 'receptionist')


class IsLabTech(BasePermission):
    def has_permission(self, request, view):
        return has_role(request.user, 'super_admin', 'lab_tech')


class BranchScopedPermission(BasePermission):
    """Rejects requests where request.branch is not set."""

    def has_permission(self, request, view):
        return (request.user.is_authenticated and
                request.branch is not None)


class VisitNotLocked(BasePermission):
    """Use as object-level permission on Visit instances."""

    def has_object_permission(self, request, view, obj):
        return not obj.is_locked
