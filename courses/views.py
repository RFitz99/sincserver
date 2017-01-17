from rest_framework import viewsets

from courses.models import Certificate, Course, CourseEnrolment
from courses.serializers import CertificateSerializer, CourseSerializer, CourseEnrolmentSerializer

class CourseViewSet(viewsets.ModelViewSet):

    queryset = Course.objects.all()
    serializer_class = CourseSerializer

    ###########################################################################
    # TODO (17/01/2017):
    # Most of the tests are failing because access controls to courses
    # are excessively permissive. We need to work out what combination of
    # permissions to apply to each action (create, update, etc.) in order
    # to confirm the assumptions being made in the tests.
    ###########################################################################
    # permission_classes = (,)

    def perform_create(self, serializer):
        # When a non-admin creates a course, we'll set them as the
        # creator and the organizer by default.
        creator = self.request.user
        organizer = self.request.user
        region = self.request.user.club.region
        # Allow staff members to set these fields explicitly
        if self.request.user.is_staff and ('organizer' in self.request.data):
            # TODO: implement this
            pass
        instance = serializer.save(
            creator=creator,
            organizer=organizer,
            region=region,
        )

    def list(self, request, region_pk=None):
        # TODO: If the request contains a region ID, then filter the
        # queryset to return only courses from that region.
        return super(CourseViewSet, self).list(request)

class CourseEnrolmentViewSet(viewsets.ModelViewSet):

    queryset = CourseEnrolment.objects.all()
    serializer_class = CourseEnrolmentSerializer

class CertificateViewSet(viewsets.ModelViewSet):

    queryset = Certificate.objects.all()
    serializer_class = CertificateSerializer
