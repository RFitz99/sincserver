from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.response import Response

from qualifications.models import Qualification
from qualifications.serializers import QualificationSerializer

class QualificationViewSet(viewsets.ViewSet):

    queryset = Qualification.objects.all()

    def list(self, request, user_pk=None):
        qualifications = self.queryset.filter(user=user_pk).order_by('-date_granted')
        serializer = QualificationSerializer(qualifications, many=True)
        return Response(serializer.data)
