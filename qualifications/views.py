from django.shortcuts import render
from rest_condition import C
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated, SAFE_METHODS
from rest_framework.response import Response

from permissions.permissions import IsAdminUser, IsSafeMethod
from users.models import User
from .models import Certificate, Qualification
from .serializers import QualificationSerializer, QualificationWriteSerializer

class QualificationViewSet(viewsets.ModelViewSet):

    # Users must be authenticated, and only admins can make changes
    permission_classes = [C(IsAuthenticated) & (C(IsAdminUser) | C(IsSafeMethod))]
    queryset = Qualification.objects.all()
    serializer_class = QualificationSerializer

    # We want clients to be able to send flat data, e.g.:
    # {'user': 1, 'certificate': 10}
    # while receiving nested data, so we'll use two different serializers.
    def get_serializer(self, *args, **kwargs):
        kwargs['context'] = self.get_serializer_context()
        if self.action in SAFE_METHODS:
            return QualificationSerializer(*args, **kwargs)
        return QualificationWriteSerializer(*args, **kwargs)

    # Filter the queryset based on the user. Admins can see everything;
    # DOs can see qualifications issued to members of their own club;
    # other users can only see qualifications they've received.
    def get_queryset(self):
        queryset = Qualification.objects.all()
        user = self.request.user
        if user.is_staff:
            return queryset
        if user.is_dive_officer():
            return queryset.filter(user__club=user.club)
        return queryset.filter(user=user)

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
