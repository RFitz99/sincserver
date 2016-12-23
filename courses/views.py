from rest_framework import viewsets

from courses.models import Certificate, Course
from courses.serializers import CertificateSerializer, CourseSerializer

class CourseViewSet(viewsets.ModelViewSet):

    queryset = Course.objects.all()
    serializer_class = CourseSerializer


class CertificateViewSet(viewsets.ModelViewSet):

    queryset = Certificate.objects.all()
    serializer_class = CertificateSerializer
