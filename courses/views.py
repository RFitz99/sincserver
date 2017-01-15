from rest_framework import viewsets

from courses.models import Certificate, Course, CourseEnrolment
from courses.serializers import CertificateSerializer, CourseSerializer, CourseEnrolmentSerializer

class CourseViewSet(viewsets.ModelViewSet):

    queryset = Course.objects.all()
    serializer_class = CourseSerializer

    def perform_create(self, serializer):
        creator = self.request.user
        organizer = self.request.user
        club = self.request.user.club
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
