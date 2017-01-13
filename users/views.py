from django.shortcuts import get_object_or_404, render
from rest_condition import C
from rest_framework import viewsets
from rest_framework.decorators import detail_route, list_route, permission_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from clubs.models import Club, CommitteePosition
from clubs.roles import DIVE_OFFICER
from clubs.serializers import CommitteePositionSerializer
from courses.models import Course
from courses.serializers import CourseSerializer
from permissions.permissions import IsAdminUser, IsDiveOfficer, IsSameUser
from users import fieldsets
from users.models import User
from users.serializers import UserSerializer

class UserViewSet(viewsets.ModelViewSet):

    # Our default permission classes: you must be authenticated to do
    # anything.
    # TODO: this should be exceptionally tight: IsAdminUser at least.
    permission_classes = (IsAdminUser,)

    # Our default queryset. This is defensive programming: if all else
    # fails, the requesting user will be sent an empty list.
    queryset = User.objects.none()

    # We use the UserSerializer class, by default, to turn User objects
    # into their JSON representations.
    serializer_class = UserSerializer

    # The permissions that the requesting user must have depend on what
    # the user is trying to do: for example, Dive Officers can create
    # new users, but we only want system administrators (who will know
    # what they're doing) to be able to delete users, while every user
    # is allowed to edit their own profile.
    permission_classes_by_action = {
        # Admins and Dive Officers can create users
        'create': [C(IsAdminUser) | C(IsDiveOfficer)],
        # Admins can update anyone; DOs can update members of their club;
        # users can update themselves
        'update': [(C(IsAdminUser) | C(IsDiveOfficer)) | C(IsSameUser)],
        # Only admins can delete users
        'delete': [IsAdminUser],
        # Admins and DOs can list users (but the queryset needs to be
        # filtered
        'list': [C(IsAdminUser) | C(IsDiveOfficer)],
        # Admins and DOs can retrieve users (but the queryset needs to
        # be filtered)
        'retrieve': [C(IsAdminUser) | C(IsDiveOfficer)],
        # Authenticated users can view their own profile
        'me': [IsAuthenticated],
    }

    # When deciding what list of permissions to check, try first to
    # find a list specified by 'permission_classes_by action'. Fall back
    # to using the default permission classes.
    #
    # Because all user-related options require the user to be authenticated,
    # we prepend IsAuthenticated to the list
    def get_permissions(self):
        try:
            return [IsAuthenticated()] + [permission() for permission in self.permission_classes_by_action[self.action]]
        except KeyError:
            return [IsAuthenticated()] + [permission() for permission in self.permission_classes]

    # When we actually go ahead and create a new User object, we want to be
    # able to assign some attributes that we don't require (or allow)
    # the requesting user to specify. We do that here.
    def perform_create(self, serializer):
        # When we create a new user, they should be added to a club if at all possible;
        # either a superuser/staff member explicitly includes a club ID in the
        # request, or a Dive Officer is creating a member (in which case we'll
        # use their club)

        # Initially, club is None. We'll try to assign one.
        club = None
        # If the user is an admin, then let them specify the club.
        if self.request.user.is_superuser or self.request.user.is_staff:
            if 'club' in self.request.data:
                club = get_object_or_404(Club, pk=self.request.data['club'])
        # Otherwise, the club should be the same as the
        # requesting user's club.
        else:
            club = self.request.user.club
        # Save the instance.
        instance = serializer.save(club=club)

    # By default, when we are coming up with a list, what we do is
    # check the user's committee standing. If they hold a committee
    # position, they are allowed (at most) to view a list of members
    # of their own club; otherwise they are allowed to view a list
    # containing exactly one User: themselves.
    def get_queryset(self):
        # Find the user making the request
        user = self.request.user

        # Admins can view everyone
        if user.is_staff:
            return User.objects.all()

        # TODO: We'll want a more sophisticated system eventually,
        # but for the moment we'll just filter by club committee position;
        # if you're on the committee, you can see what's going on.
        # Field restrictions are specified in serializers.py.
        if CommitteePosition.objects.filter(user=user, club=user.club).exists():
            return User.objects.filter(club=user.club)
        return User.objects.filter(id=user.id)


    # When the user asks for a list of Users, check their status and
    # filter the queryset accordingly.
    def list(self, request, club_pk=None, region_pk=None):
        # Our permission_classes setting for list actions means that
        # the user is either an admin or a dive officer. If the user
        # is an admin, we'll let them view the whole list of users;
        # otherwise, we'll filter to limit results to the DO's club.

        # Find the user making the request.
        user = self.request.user

        # Set the initial queryset. If the user is an admin, then
        # they can view the entire list.
        if user.is_staff:
            queryset = User.objects.all()
        # If the user is not an admin, then they're a DO; return
        # only the members of their club.
        else:
            queryset = User.objects.filter(club=user.club)

        # If we are looking for the users within a specific club
        # (e.g., an admin has made the request), then filter further.
        if club_pk is not None:
            queryset = queryset.filter(club__id=club_pk)

        # Serialize the queryset to JSON.
        serializer = self.serializer_class(queryset, many=True)

        # Return a Response.
        return Response(serializer.data)


    ###########################################################################
    # Extra routes
    ###########################################################################

    # Tell us which courses this user has organized.
    @detail_route(methods=['get'], url_path='courses-organized')
    def courses_organized(self, request, pk=None):
        """
        Return the list of courses that this user has organized.
        """
        user = self.get_object()
        courses = Course.objects.filter(organizer=user)
        serializer = CourseSerializer(courses, many=True)
        return Response(serializer.data)


    # Tell us which courses this user has organized.
    @detail_route(methods=['get'], url_path='courses-taught')
    def courses_taught(self, request, pk=None):
        """
        Return the list of courses on which this user is teaching
        or has taught
        """
        user = self.get_object()
        courses = Course.objects.filter(instructors=user)
        serializer = CourseSerializer(courses, many=True)
        return Response(serializer.data)


    # Return this user's current membership status.
    @detail_route(methods=['get'])
    def current_membership_status(self, request, pk=None):
        """
        Return this user's current membership status
        """
        # TODO: 
        user = self.get_object()
        fields = fieldsets.MEMBERSHIP_STATUS
        serializer = UserSerializer(user, fields=fields)
        return Response(serializer.data)


    # Return the requesting user's own profile. This method
    # doesn't require us to know the user's ID; we get it
    # from the request (which automatically does a DB lookup
    # to populate its 'user' attribute anyway).
    @list_route(methods=['get'])
    def me(self, request):
        """
        Return the requesting user's profile information.
        """
        fields = fieldsets.OWN_PROFILE
        serializer = UserSerializer(request.user, fields=fields)
        return Response(serializer.data)
