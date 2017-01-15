from rest_framework import viewsets

from courses.models import Certificate, Course, CourseEnrolment
from courses.serializers import CertificateSerializer, CourseSerializer, CourseEnrolmentSerializer

class CourseViewSet(viewsets.ModelViewSet):

    queryset = Course.objects.all()
    serializer_class = CourseSerializer

class CourseEnrolmentViewSet(viewsets.ModelViewSet):

    queryset = CourseEnrolment.objects.all()
    serializer_class = CourseEnrolmentSerializer


class CertificateViewSet(viewsets.ModelViewSet):

    queryset = Certificate.objects.all()
    serializer_class = CertificateSerializer
