from rest_framework import viewsets
from rest_framework.decorators import detail_route, list_route, permission_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from rest_condition import C, ConditionalPermission

from clubs.models import Club, Region
from clubs.roles import DIVE_OFFICER
from clubs.serializers import ClubSerializer, RegionSerializer
from permissions.permissions import IsAdminUser, IsRegionalDiveOfficer, IsDiveOfficer, IsSafeMethod
from qualifications.models import Qualification
from qualifications.serializers import QualificationSerializer
from users.models import User
from users.serializers import UserSerializer

from users.choices import STATUS_CURRENT

class ClubViewSet(viewsets.ModelViewSet):

    ###########################################################################
    # Field sets for detail views
    ###########################################################################
    # By default, only ID, name, and region are available
    base_fields = ('id', 'name', 'region')
    # Admins can see everything, but we'll enumerate the fields
    # explicitly
    admin_fields = base_fields + (
        'creation_date',
        'foundation_date',
        'last_modified',
        'users',
    )
    # DOs can see extra information about their own clubs
    do_fields = base_fields + (
        'foundation_date',
        'users',
    )

    # Permissions for viewing clubs.
    # 1. User must be authenticated.
    # 2. Only admins can perform unsafe (CUD) operations
    permission_classes = [
        # 1. User must be authenticated
        IsAuthenticated,
        # 2. Only admins may perform unsafe operations
        (C(IsAdminUser) | C(IsSafeMethod)),
    ]

    permission_classes_by_action = {
        # We don't allow regular users to list all clubs
        'list': [C(IsAdminUser) | C(IsDiveOfficer)],
    }

    def get_permissions(self):
        try:
            return [IsAuthenticated()] + [permission() for permission in \
                                          self.permission_classes_by_action[self.action]]
        except KeyError:
            return [IsAuthenticated()] + [permission() for permission in \
                                          self.permission_classes]

    queryset = Club.objects.all()
    serializer_class = ClubSerializer

    def retrieve(self, request, pk=None):
        club = self.get_object()
        user = request.user
        # By default, a club detail response will contain only
        # the club's ID, name, and its region ID
        fields = self.base_fields
        # Admins can see everything, however
        if user.is_staff:
            fields = self.admin_fields
        # Let DOs see more detail about their own club
        if user.is_dive_officer() and user.club == club:
            fields = self.do_fields
        serializer = self.serializer_class(club, fields=fields)
        return Response(serializer.data)

    # Given a club ID in the request URL, find all qualifications that
    # have been granted to members of that club
    @detail_route(methods=['GET'])
    def qualifications(self, request, pk=None):
        club = self.get_object()
        # the requesting user is a superuser or staff, then that's OK.
        if request.user.is_superuser or request.user.is_staff:
            pass
        # Regular users can't access this at all
        elif not request.user.has_any_role():
            raise PermissionDenied
        # A Dive Officer can only receive a list of members of their own club
        elif not club == request.user.club:
            raise PermissionDenied
        # Otherwise, proceed
        queryset = Qualification.objects.filter(user__club=club)
        serializer = QualificationSerializer(queryset, many=True)
        return Response(serializer.data)


class RegionViewSet(viewsets.ModelViewSet):

    queryset = Region.objects.all()

    # Permissions for regions.
    # 1. User must be authenticated to view.
    # 2. Only admins can perform unsafe (CUD) operations.
    permission_classes = [
        # User must be authenticated
        IsAuthenticated,
        # Only admins may perform unsafe operations
        (C(IsAdminUser) | C(IsSafeMethod)),
    ]

    serializer_class = RegionSerializer

    @detail_route(methods=['GET'], url_path='active-instructors')
    def active_instructors(self, request, pk=None):
        """
        Return a list of the active instructors in the region.
        Admins can see this list, as can committee members of clubs in the region
        and the region's Dive Officer. Everyone else is forbidden.
        """
        # Get the region
        region = self.get_object()
        # Get the requesting user
        user = self.request.user

        # If the user is an admin, then they're fine
        if user.is_staff:
            pass
        # Otherwise, if the user is a committee member and the region
        # matches, then they're fine
        elif user.has_any_role() and user.club.region == region:
            pass
        # Or (least likely) the user is the regional dive officer
        elif user == region.dive_officer:
            pass
        # Otherwise, they're forbidden to access this
        else:
            raise PermissionDenied

        # Get all instructors from this region
        queryset = User.objects.filter(
            club__region=region,
            qualifications__certificate__is_instructor_certificate=True
        )
        # Filter on active status --- we can't do this through the ORM,
        # so we have to do it on the retrieved queryset.
        queryset = [u for u in queryset if u.current_membership_status() == STATUS_CURRENT]
        serializer = UserSerializer(queryset, many=True)
        return Response(serializer.data)

    @detail_route(methods=['get'])
    def dive_officers(self, request, pk=None):
        """
        Return a list of club dive officers with their contact details.
        This is only available to system administrators (who can see
        all of the DOs or filter by region) and club Dive Officers
        (who can see DOs in their region).
        """
        region = self.get_object()

        # TODO: allow RDOs to see DOs in their region
        user = request.user
        if not (user.is_admin() or user.is_dive_officer()):
            raise PermissionDenied

        # We want users from this region who are dive officers
        queryset = User.objects.filter(club__region=region, committee_positions__role=DIVE_OFFICER)

        # We only want the contact details of these Dive Officers
        fields = fieldsets.CONTACT_DETAILS

        # Serialize and return the data
        serializer = UserSerializer(dive_officers, fields=fields, many=True)
        return Response(serializer.data)
