from rest_framework import viewsets
from rest_framework.decorators import detail_route, permission_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from clubs.models import Club, Region
from clubs.serializers import RegionSerializer
from permissions.permissions import IsAdminOrReadOnly, IsDiveOfficer
from qualifications.models import Qualification
from qualifications.serializers import QualificationSerializer
from users.models import User
from users.serializers import UserSerializer

from users.choices import STATUS_CURRENT

class ClubViewSet(viewsets.ModelViewSet):
    
    # TODO: check object permissions

    queryset = Club.objects.all()

    @detail_route(methods=['GET'])
    def qualifications(self, request, pk=None):
        club = self.get_object()
        # the requesting user is a superuser or staff, then that's OK
        if request.user.is_superuser or request.user.is_staff:
            pass
        # Regular users can't access this at all
        elif not request.user.has_any_role():
            raise PermissionDenied
        # A Dive Officer can only receive a list of members of their own club
        elif not club == request.user.club:
            raise PermissionDenied
        # Otherwise, proceed
        queryset = Qualification.objects.filter(user__club=club)
        serializer = QualificationSerializer(queryset, many=True)
        return Response(serializer.data)

    @detail_route(methods=['GET'])
    def users(self, request, pk=None):
        club = self.get_object()
        # the requesting user is a superuser or staff, then that's OK
        if request.user.is_superuser or request.user.is_staff:
            pass
        # Regular users can't access this at all
        elif not request.user.has_any_role():
            raise PermissionDenied
        # A Dive Officer can only receive a list of members of their own club
        elif not club == request.user.club:
            raise PermissionDenied
        # Otherwise, proceed
        queryset = User.objects.filter(club=club)
        serializer = UserSerializer(queryset, many=True)
        return Response(serializer.data)


class RegionViewSet(viewsets.ModelViewSet):

    queryset = Region.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = RegionSerializer

    @detail_route(methods=['GET'], url_path='active-instructors')
    def active_instructors(self, request, pk=None):
        """
        Return a list of the active instructors in the region.
        """
        # Check user's permission to view
        user = self.request.user
        if not (user.is_admin() or user.has_any_role()):
            raise PermissionDenied

        region = self.get_object()
        # Get all instructors from this region
        queryset = User.objects.filter(
            club__region=region,
            qualifications__certificate__is_instructor_certificate=True
        )
        # Filter on active status --- we can't do this through the ORM,
        # so we have to do it on the retrieved queryset.
        queryset = [u for u in queryset if u.current_membership_status() == STATUS_CURRENT]
        serializer = UserSerializer(queryset, many=True)
        return Response(serializer.data)
