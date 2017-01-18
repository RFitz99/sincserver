from rest_framework import viewsets
from rest_framework.decorators import detail_route, list_route, permission_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import SAFE_METHODS, IsAuthenticated
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

    queryset = Club.objects.all()
    serializer_class = ClubSerializer

    ###########################################################################
    # Field sets for detail views --- these tuples 
    ###########################################################################

    # By default, these fields are made available to any authenticated user.
    base_fields = (
        'contact_email',
        'contact_name',
        'contact_phone',
        'description',
        'id',
        'location',
        'name',
        'region',
        'training_times',
    )

    # Admins can see everything, but we'll enumerate the fields
    # explicitly, to be on the safe side.
    admin_fields = base_fields + (
        'creation_date',
        'foundation_date',
        'last_modified',
        'users',
    )

    # DOs can see extra information about their own clubs.
    do_fields = base_fields + (
        'foundation_date',
        'users',
    )

    # Default permissions for viewing clubs.
    # 1. User must be authenticated.
    # 2. Only admins can perform unsafe (CUD) operations
    permission_classes = [
        # 1. User must be authenticated
        IsAuthenticated,
        # 2. Only admins may perform unsafe operations
        (C(IsAdminUser) | C(IsSafeMethod)),
    ]

    # Action-specific permission classes, which override the defaults.
    permission_classes_by_action = {
        # Only admins can create new clubs
        'create': [C(IsAdminUser)],
        # Only admins can delete clubs
        'destroy': [C(IsAdminUser)],
        # Admins and DOs can retrieve club lists
        'list': [C(IsAdminUser) | C(IsDiveOfficer)],
        # Admins and DOs can update
        'update': [C(IsAdminUser) | C(IsDiveOfficer)],
    }

    def get_allowed_fields(self, user, club):
        if self.action in SAFE_METHODS:
            # By default, the allowed fields
            # the club's ID, name, and its region ID
            fields = self.base_fields
            # Admins can see everything, however
            if user.is_staff:
                fields = self.admin_fields
            # Let DOs see more detail about their own club
            if user.is_dive_officer() and user.club == club:
                fields = self.do_fields
            return fields
        # For *unsafe* methods, we are a little stricter: DOs may
        # not change their club's name or region. Only admins
        # can do that.
        if user.is_staff:
            return self.admin_fields
        if club.has_as_dive_officer(user):
            # Remove name and region from allowed fields
            return tuple(set(self.do_fields) - set(['name', 'region']))

        # We shouldn't be here. A non-admin, non-DO user has no rights
        # to change any aspect of their club (and they should have been
        # caught during the permissions check), so just raise PermissionDenied
        raise PermissionDenied

    # Try to find an action-specific list of permission classes,
    # falling back to the (tighter) defaults.
    def get_permissions(self):
        try:
            return [IsAuthenticated()] + [permission() for permission in \
                                          self.permission_classes_by_action[self.action]]
        except KeyError:
            return [IsAuthenticated()] + [permission() for permission in \
                                          self.permission_classes]

    # We override ModelViewSet.retrieve() in order to set the fields.
    def retrieve(self, request, pk=None):
        # Retrieve the club
        club = self.get_object()
        # Get the requesting user
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

    # The user can update different parts of the Club object based on
    # who they are: admins can change everything; DOs aren't permitted to
    # change the club's name or region; and so on. When we're performing
    # an update, we check the fields in the incoming request, compare them
    # with the fields that the user is allowed to update, and tell the
    # serializer to handle only the fields that are in both sets.
    #
    # Apart from that, the code is simply copied from
    # rest_framework.generics.UpdateModelMixin.
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        # Get the fields that the user is allowed to update
        allowed_fields = set(self.get_allowed_fields(request.user, instance))
        # Get the fields that the user wants to update
        requested_fields = set([k for k in request.data])
        # Find the intersection of the two sets --- these are the ones we'll update
        fields = allowed_fields.intersection(requested_fields)
        # Invoke our serializer, passing the fields as a keyword argument
        serializer = self.get_serializer(instance, data=request.data, fields=fields, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # refresh the instance from the database.
            instance = self.get_object()
            # Again, pass in the 'fields' kwarg to ensure we don't accidentally
            # expose sensitive information
            serializer = self.get_serializer(instance, fields=fields)

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
