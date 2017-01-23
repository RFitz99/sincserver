from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.response import Response

from permissions.permissions import IsAdminUser
from qualifications.models import Qualification
from qualifications.serializers import QualificationSerializer

class QualificationViewSet(viewsets.ViewSet):

    queryset = Qualification.objects.all()

    def list(self, request, user_pk=None):
        qualifications = self.queryset
        if user_pk is not None:
            qualifications = self.queryset.filter(user=user_pk)

        user = request.user
        if not user.is_staff:
            if user.is_dive_officer():
                qualifications = qualifications.filter(user__club=user.club)
            else:
                qualifications = qualifications.filter(user=user)
        qualifications = qualifications.order_by('-date_granted')
        serializer = QualificationSerializer(qualifications, many=True)
        return Response(serializer.data)
