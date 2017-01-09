from rest_framework import viewsets
from rest_framework.decorators import detail_route, list_route, permission_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from clubs.models import Club, Region
from clubs.serializers import RegionSerializer
from permissions.permissions import IsAdminOrDiveOfficer, IsAdminOrReadOnly, IsDiveOfficer
from qualifications.models import Qualification
from qualifications.serializers import QualificationSerializer
from users.models import User
from users.serializers import UserSerializer

from users.choices import STATUS_CURRENT

class ClubViewSet(viewsets.ModelViewSet):
    
    # TODO: check object permissions
    permission_classes= (IsAdminOrDiveOfficer,)

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

    @list_route(methods=['get'])
    def dive_officers(self, request):
        """
        Return a list of club dive officers with their contact details.
        This is only available to system administrators (who can see
        all of the DOs or filter by region) and club Dive Officers
        (who can see DOs in their region).
        """
        # TODO: allow RDOs to see DOs in their region
        user = request.user
        if not (user.is_admin() or user.is_dive_officer()):
            raise PermissionDenied

        # We only want Dive Officers
        queryset = User.objects.filter(committee_positions__role=DIVE_OFFICER)

        # If the user is an admin, they can opt to filter by region or
        # just see all Dive Officers
        if user.is_admin():
            if 'region' in request.data:
                queryset = queryset.filter(club__region=request.data['region'])
        else:
            queryset = queryset.filter(club__region=user.club.region)

        # We only want the contact details of these Dive Officers
        fields = fieldsets.CONTACT_DETAILS

        # Serialize and return the data
        serializer = UserSerializer(dive_officers, fields=fields, many=True)
        return Response(serializer.data)


class RegionViewSet(viewsets.ModelViewSet):

    queryset = Region.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = RegionSerializer

    @detail_route(methods=['GET'], url_path='active-instructors')
    def active_instructors(self, request, pk=None):
        """
        Return a list of the active instructors in the region.
        Admins can see this list, as can committee members of clubs in the region
        and the region's Dive Officer. Everyone else is forbidden.
        """
        # Get the region
        region = self.get_object()
        # Get the requesting user
        user = self.request.user

        # If the user is an admin, then they're fine
        if user.is_admin():
            pass
        # Otherwise, if the user is a committee member and the region
        # matches, then they're fine
        elif user.has_any_role() and user.club.region == region:
            pass
        # Or (least likely) the user is the regional dive officer
        elif region.dive_officer == user:
            pass
        # Otherwise, they're forbidden
        else:
            raise PermissionDenied

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
