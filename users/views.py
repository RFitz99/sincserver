from django.shortcuts import get_object_or_404, render
from rest_framework import viewsets
from rest_framework.decorators import detail_route, list_route, permission_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from clubs.models import Club, CommitteePosition
from clubs.serializers import CommitteePositionSerializer
from courses.models import Course
from courses.serializers import CourseSerializer
from permissions import permissions
from users import fieldsets
from users.models import User
from users.serializers import UserSerializer

# Create your views here.
class UserViewSet(viewsets.ModelViewSet):

    permission_classes = (IsAuthenticated,)

    queryset = User.objects.none() # Default to nothing, just for safety
    serializer_class = UserSerializer

    permission_classes_by_action = {
        # Dive Officers can create users
        'create': [permissions.IsAdminOrDiveOfficer],
        # Users can update their own profiles
        'update': [permissions.IsDiveOfficerOrOwnProfile],
        # Only admins can delete users
        'delete': [IsAdminUser],
    }

    def create(self, request):
        return super(UserViewSet, self).create(request)

    def get_permissions(self):
        # TODO: Rather than enumerate these explicitly here, we should
        # do something more elegant. (I just need to work out what that is.)
        try:
            return [permission() for permission in self.permission_classes_by_action[self.action]]
        except KeyError:
            return [permission() for permission in self.permission_classes]

    def perform_create(self, serializer):
        # When we create a new user, they should be added to a club if at all possible;
        # either a superuser/staff member explicitly includes a club ID in the
        # request, or a Dive Officer is creating a member (in which case we'll
        # use their club)
        if self.request.user.is_superuser or self.request.user.is_staff:
            if 'club' in self.request.data:
                club = get_object_or_404(Club, pk=self.request.data['club'])
        else:
            club = self.request.user.club
        instance = serializer.save(club=club)

    def get_queryset(self):
        user = self.request.user # This is the user making the request

        # TODO: We'll want a more sophisticated system eventually,
        # but for the moment we'll just filter by club committee position;
        # if you're on the committee, you can see what's going on.
        # Field restrictions are specified in serializers.py
        if CommitteePosition.objects.filter(user=user, club=user.club).exists():
            return User.objects.filter(club=user.club)
        return User.objects.filter(id=user.id)

    def list(self, request):
        queryset = User.objects.none()
        if self.request.user.is_superuser:
            queryset = User.objects.all()
        elif self.request.user.has_any_role():
            queryset = User.objects.filter(club=self.request.user.club)
        else:
            queryset = User.objects.filter(user=self.request.user)
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)

    @list_route(methods=['get'], url_path='active-instructors')
    def active_instructors(self, request):
        """
        Return a list of those active instructors that the requesting
        user is allowed to view.
        """
        user = request.user
        # Lists of active instructors are available to staff,
        # club DOs, and noone else
        if not (user.is_admin() or user.is_dive_officer()):
            raise PermissionDenied

        # Queryset is initially all instructors
        queryset = User.objects.filter(qualifications__certificate__is_instructor_certificate=True)

        # If the user isn't staff, then filter to the region
        if not (user.is_staff or user.is_superuser):
            queryset = queryset.filter(club__region=user.club.region)

        # Serialize the queryset and return it
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)


    @list_route(methods=['get'])
    def me(self, request):
        """
        Return the requesting user's profile information.
        """
        fields = fieldsets.OWN_PROFILE
        serializer = UserSerializer(request.user, fields=fields)
        return Response(serializer.data)


    @detail_route(methods=['get'], url_path='courses-organized')
    def courses_organized(self, request, pk=None):
        user = self.get_object()
        courses = Course.objects.filter(organizer=user)
        serializer = CourseSerializer(courses, many=True)
        return Response(serializer.data)

    @detail_route(methods=['get'], url_path='courses-taught')
    def courses_taught(self, request, pk=None):
        user = self.get_object()
        courses = Course.objects.filter(instructors=user)
        serializer = CourseSerializer(courses, many=True)
        return Response(serializer.data)

    @detail_route(methods=['get'])
    def current_membership_status(self, request, pk=None):
        user = self.get_object()
        fields = fieldsets.MEMBERSHIP_STATUS
        serializer = UserSerializer(user, fields=fields)
        return Response(serializer.data)

    # TODO: restrict this information to committee members
    @list_route(methods=['get'])
    def dive_officers(self, request):
        """
        Return a list of club dive officers with their contact details.
        """
        user = request.user
        if not (user.is_admin() or user.is_dive_officer()):
            raise PermissionDenied
        fields = fieldsets.CONTACT_DETAILS
        # TODO: can we pass a lambda to filter()?
        dive_officers = User.objects.none()
        serializer = UserSerializer(dive_officers, fields=fields, many=True)
        return Response(serializer.data)

    # TODO: restrict this information to committee members
    @list_route(methods=['get'])
    def current_instructors(self, request):
        pass
