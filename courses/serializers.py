from rest_framework.serializers import IntegerField, ListSerializer, ModelSerializer

from clubs.serializers import RegionSerializer
from courses.models import Certificate, Course, CourseEnrolment, CourseInstruction
from serializers import DynamicFieldsModelSerializer
from users.serializers import UserSerializer

class CertificateSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = Certificate
        fields = ('id', 'name',)

class CourseEnrolmentSerializer(ModelSerializer):
    class Meta:
        model = CourseEnrolment
        fields = '__all__'

class CourseSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = Course
        fields = (
            'certificate',
            'creator',
            'id',
            'maximum_participants',
            'organizer',
            'region',
            'datetime',
        )
    # Course creator and course organizer are handled in the view
    # (they are set to the requesting user unless that user is an
    # admin), so we set them as read_only here.
    creator = UserSerializer(fields=('id', 'first_name', 'last_name', 'email',), read_only=True)
    organizer = UserSerializer(fields=('id', 'first_name', 'last_name', 'email',), read_only=True)
    certificate = CertificateSerializer(fields=('id', 'name'), read_only=True)
    maximum_participants = IntegerField(required=False, allow_null=True)
    region = RegionSerializer(read_only=True)


class CourseInstructionSerializer(ModelSerializer):
    class Meta:
        model = CourseInstruction
        fields = (
            'id',
            'user',
            'course',
        )

    user = UserSerializer(fields=('id', 'first_name', 'last_name', 'email',), read_only=True)
    course = CourseSerializer(fields=('id', 'certificate', 'creator', 'organizer', 'region'), read_only=True)
