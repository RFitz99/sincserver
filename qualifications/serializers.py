from rest_framework import serializers

from qualifications.models import Certificate, Qualification
from users.serializers import UserSerializer

class CertificateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Certificate
        fields = ('id', 'name',)

class QualificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Qualification
        fields = ('user', 'certificate', 'date_granted',)
    user = UserSerializer(fields=['id', 'first_name', 'last_name'])
    certificate = CertificateSerializer()
