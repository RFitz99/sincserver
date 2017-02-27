from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_condition import C
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated, SAFE_METHODS
from rest_framework.response import Response

from permissions.permissions import IsAdminUser, IsDiveOfficer, IsSafeMethod, IsUser
from users.models import User
from .models import Certificate, Qualification
from .serializers import QualificationSerializer, QualificationWriteSerializer

class QualificationViewSet(viewsets.ModelViewSet):

    # Users must be authenticated, and only admins can make changes
    permission_classes = [
        C(IsAuthenticated),
        (C(IsAdminUser) | C(IsSafeMethod))
    ]
    queryset = Qualification.objects.all()
    serializer_class = QualificationSerializer

    # We want clients to be able to send flat data, e.g.:
    # {'user': 1, 'certificate': 10}
    # while receiving nested data, so we'll use two different serializers.
    def get_serializer(self, *args, **kwargs):
        kwargs['context'] = self.get_serializer_context()
        if self.request.method in SAFE_METHODS:
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
        qualifications = self.get_queryset()
        user = self.request.user
        if not user.is_staff:
            if user.is_dive_officer():
                qualifications = qualifications.filter(user__club=user.club)
            else:
                qualifications = qualifications.filter(user=user)
        if user_pk is not None:
            # We'll allow a nested list request if the requesting user is
            # an admin, or if the user is looking for their own qualifications.
            # TODO: Doing this manually is really brittle. It would be
            # much better if drf-nested-routers could do this for us. See:
            # https://github.com/alanjds/drf-nested-routers/issues/73
            target_user = get_object_or_404(User, pk=user_pk)
            if user.is_staff or user == target_user or target_user.has_as_dive_officer(user):
                qualifications = qualifications.filter(user=user_pk)
            else:
                raise Http404

        qualifications = qualifications.order_by('-date_granted')
        serializer = QualificationSerializer(qualifications, many=True)
        return Response(serializer.data)
