from rest_framework.serializers import ModelSerializer

from clubs.serializers import RegionSerializer
from courses.models import Certificate, Course
from users.serializers import UserSerializer

class CertificateSerializer(ModelSerializer):
    class Meta:
        model = Certificate
        fields = ('id', 'name',)

class CourseSerializer(ModelSerializer):
    class Meta:
        model = Course
        fields = (
                'certificate',
                'creator',
                'id',
                'organizer',
                'region',
                )
    certificate = CertificateSerializer()
    creator = UserSerializer(fields=('id', 'first_name', 'last_name',))
    organizer = UserSerializer(fields=('id', 'first_name', 'last_name', 'email',))
    region = RegionSerializer()
