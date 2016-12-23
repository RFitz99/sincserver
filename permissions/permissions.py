from rest_framework import permissions

from clubs.models import CommitteePosition
from clubs.roles import DIVE_OFFICER
from users.models import User

class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff

class IsDiveOfficer(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_dive_officer()
    
    def has_object_permission(self, request, *args, **kwargs):
        return request.user.is_dive_officer()

class IsDiveOfficerOrReadOnly(permissions.BasePermission):
    """
    Checks whether the requesting user is a Dive Officer of their club
    """
    def has_permission(self, request, view):
        # Read-only methods are OK
        if request.method in permissions.SAFE_METHODS:
            return True
        # Otherwise, check whether a DO committee position exists for this user
        # and return True or False
        return request.user.is_dive_officer()

class IsDiveOfficerOrOwnProfile(permissions.BasePermission):
    """
    """
    def has_permission(self, request, view):
        pass

class IsCommitteeMember(permissions.BasePermission):

    def has_permission(self, request, view):
        return request.user.has_any_role()


class IsAdminOrDiveOfficer(permissions.BasePermission):

    def has_permission(self, request, view):
        return request.user.is_superuser or request.user.is_staff or request.user.is_dive_officer()
