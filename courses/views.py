from rest_condition import C
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from courses.models import Certificate, Course, CourseEnrolment
from courses.serializers import CertificateSerializer, CourseSerializer, CourseEnrolmentSerializer
from permissions.permissions import IsAdminUser, IsDiveOfficer, IsSafeMethod
from users.models import User

class CourseViewSet(viewsets.ModelViewSet):

    queryset = Course.objects.all()
    serializer_class = CourseSerializer

    ###########################################################################
    # TODO (17/01/2017):
    # Most of the tests are failing because access controls to courses
    # are excessively permissive. We need to work out what combination of
    # permissions to apply to each action (create, update, etc.) in order
    # to confirm the assumptions being made in the tests.
    #
    # Check the permissions code for UserViewSet (in users/views.py) for
    # an example of how to do this.
    ###########################################################################
    permission_classes = (C(IsAdminUser) | C(IsSafeMethod),)

    permission_classes_by_action = {
        'create': [C(IsAdminUser) | C(IsDiveOfficer)],
        'retrieve': [],
    }

    def get_permissions(self):
        try:
            return [IsAuthenticated()] + [permission() for permission in self.permission_classes_by_action[self.action]]
        except KeyError:
            return [IsAuthenticated()] + [permission() for permission in self.permission_classes]

    def perform_create(self, serializer):
        user = self.request.user
        # When a non-admin creates a course, we'll set them as the
        # creator and the organizer by default.
        creator = user
        organizer = user
        region = user.club.region

        # If the user is an administrator, they can override the default creator
        if user.is_staff and ('creator' in self.request.data):
            creator = User.objects.get(pk=self.request.data['creator'])

        # If the user is an admin or Dive Officer, they can
        # override the default organizer. An admin can set this to
        # any user they like, but a Dive Officer can only set the
        # organizer to a member of their own club.
        #
        # We will set the region to the organizer's region by default,
        # unless the user explicitly sets the region (handled later).
        if (user.is_staff or user.is_dive_officer()) and 'organizer' in self.request.data:
            try:
                proposed_organizer = User.objects.get(pk=self.request.data['organizer'])
                # Staff members may set any user as organizer; DOs may only set members
                # of their own club
                if user.is_staff or proposed_organizer.club == user.club:
                    organizer = proposed_organizer
            except User.DoesNotExist:
                # Fall back to setting the requesting user as the organizer
                organizer = user

        # If the user is an admin, they can override the default region.
        if user.is_staff and ('region' in self.request.data):
            # TODO: Implement this!
            pass

        # Save the instance
        instance = serializer.save(
            creator=creator,
            organizer=organizer,
            region=region,
        )

    def list(self, request, region_pk=None):
        # TODO: If the request contains a region ID, then filter the
        # queryset to return only courses from that region.
        # Check the README for drf-nested-routers for an example of
        # how to do this:
        # https://github.com/alanjds/drf-nested-routers
        return super(CourseViewSet, self).list(request)



class CourseEnrolmentViewSet(viewsets.ModelViewSet):

    queryset = CourseEnrolment.objects.all()
    serializer_class = CourseEnrolmentSerializer

class CertificateViewSet(viewsets.ModelViewSet):

    queryset = Certificate.objects.all()
    serializer_class = CertificateSerializer
