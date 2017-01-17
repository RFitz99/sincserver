from rest_framework import permissions

from clubs.models import CommitteePosition
from clubs.roles import DIVE_OFFICER
from users.models import User

class IsAdminUser(permissions.IsAdminUser):
    def has_object_permission(self, request, view, obj):
        return request.user and request.user.is_staff



class IsCommitteeMember(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.has_any_role()



class IsDiveOfficer(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_dive_officer()
    
    def has_object_permission(self, request, view, obj):
        # Try to check whether the object in question is under
        # the purview of the requesting user. This is
        # only relevant to certain model types (specifically
        # Clubs and Users), and will raise an AttributeError
        # on objects that don't have the method defined, but
        # that's OK: in that case, we just return False.
        try:
            return obj.has_as_dive_officer(request.user)
        except AttributeError:
            return False
        #return request.user.is_dive_officer() and request.user.club == obj.club



class IsSameUser(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user == obj



class IsRegionalDiveOfficer(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_regional_dive_officer()



class IsSafeMethod(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS
