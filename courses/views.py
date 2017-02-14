from django.shortcuts import get_object_or_404
from rest_condition import C
from rest_framework import status
from rest_framework import viewsets
from rest_framework.exceptions import MethodNotAllowed, PermissionDenied
from rest_framework.mixins import CreateModelMixin, DestroyModelMixin, RetrieveModelMixin, UpdateModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from clubs.models import Region
from courses.models import Certificate, Course, CourseEnrolment, CourseInstruction
from courses.serializers import CertificateSerializer, CourseSerializer, CourseEnrolmentSerializer, CourseInstructionSerializer
from mixins import PermissionClassesByActionMixin
from permissions.permissions import IsAdminUser, IsCourseOrganizer, IsCreator, \
        IsDiveOfficer, IsSafeMethod, IsSameUser, IsUser
from users.models import User

def find_organizer_or_fall_back(user, data, current_organizer=None):
    # If the user is an admin or Dive Officer, they can
    # override the default organizer. An admin can set this to
    # any user they like, but a Dive Officer can only set the
    # organizer to a member of their own club.
    #
    # We will set the region to the organizer's region by default,
    # unless the user explicitly sets the region (handled later).

    # Our fallback: the currently-set organizer
    fallback = current_organizer if current_organizer is not None else user

    # If the user is an admin or a DO, then let them try to reassign
    # the organizer if they want
    if (user.is_staff or user.is_dive_officer()) and 'organizer' in data:
        # Try and find the user by ID; if it's invalid, return the
        # fallback
        try:
            proposed_organizer = User.objects.get(pk=data['organizer'])
            # Staff members may set any user as organizer; DOs may only set members
            # of their own club
            if user.is_staff or proposed_organizer.club == user.club:
                return proposed_organizer
        except User.DoesNotExist:
            return fallback
    # If we could not assign a value to proposed_organizer, then return
    # the fallback
    return fallback

class CourseViewSet(PermissionClassesByActionMixin, viewsets.ModelViewSet):

    queryset = Course.objects.all()
    serializer_class = CourseSerializer

    permission_classes = (C(IsAdminUser) | C(IsSafeMethod),)

    permission_classes_by_action = {
        'create': [C(IsAdminUser) | C(IsDiveOfficer)],
        'partial_update': [C(IsAdminUser) | C(IsCreator)],
        'update': [C(IsAdminUser) | C(IsDiveOfficer)],
    }

    def list(self, request, region_pk=None):
        # If the request contains a region ID, then filter the
        # queryset to return only courses from that region.
        queryset = Course.objects.all()
        if region_pk is not None:
            queryset = queryset.filter(region=region_pk)
        serializer = CourseSerializer(queryset, many=True)
        return Response(serializer.data)

    def perform_create(self, serializer):
        # The requesting user
        user = self.request.user
        # The request
        request = self.request

        # By default the course creator is the requesting user
        creator = user
        # If the user is an administrator, they can override the default creator
        if user.is_staff and ('creator' in self.request.data):
            creator = User.objects.get(pk=self.request.data['creator'])

        # Find the proposed course organizer, falling back to the requesting user
        # if permissions fail or the proposed organizer can't be found.
        organizer = find_organizer_or_fall_back(user, request.data)

        # By default, the region is the region of the requesting user's club
        region = user.club.region
        # If the user is an admin, they can override the default region.
        if user.is_staff and ('region' in self.request.data):
            region = get_object_or_404(Region, pk=self.request.data['region'])

        # Find the certificate by its ID
        # TODO: this 500's if the cert ID is undefined; we need to deal with
        # this so that it returns a 4xx response.
        certificate = get_object_or_404(Certificate, pk=self.request.data['certificate'])

        # Save the instance
        instance = serializer.save(
            certificate=certificate,
            creator=creator,
            organizer=organizer,
            region=region,
        )

        # Add instructors, if specified. (This is only allowed when
        # the course is being created; otherwise it needs to be
        # performed through the CourseInstruction nested route.)
        # TODO: This may require us to lock the user table as well,
        # in which case we'll need to enforce atomicity.
        instructors = []
        if 'instructors' in self.request.data:
            instructors = User.objects.filter(id__in=self.request.data['instructors'])
        for instructor in instructors:
            CourseInstruction.objects.create(course=instance, user=instructor)

    def perform_update(self, serializer):
        user = self.request.user
        data = self.request.data
        instance = self.get_object()

        certificate = instance.certificate
        # Find the certificate by its ID
        if 'certificate' in data:
            certificate = get_object_or_404(Certificate, pk=data.get('certificate', None))

        region = instance.region
        if 'region' in data:
            region = get_object_or_404(Region, pk=data.get('region', None))

        organizer = find_organizer_or_fall_back(user, data, instance.organizer)

        updated_instance = serializer.save(
            certificate=certificate,
            organizer=organizer,
            region=region,
        )

        # TODO: This does not modify any expense types or values
        # (but then we are not currently allowing the user to set
        # them)
        if 'instructors' in data:
            instructors = User.objects.filter(id__in=data['instructors'])
            for instructor in instructors:
                CourseInstruction.objects.get_or_create(
                    course=instance,
                    user=instructor
                )

class CourseEnrolmentViewSet(PermissionClassesByActionMixin, viewsets.ModelViewSet):

    queryset = CourseEnrolment.objects.all()
    serializer_class = CourseEnrolmentSerializer

    permission_classes = [C(IsAuthenticated),]
    permission_classes_by_action = {
        'create': [C(IsAdminUser) | C(IsDiveOfficer) | C(IsSameUser)],
        'destroy': [C(IsAdminUser) | C(IsDiveOfficer) | C(IsUser)],
    }

    def get_queryset(self):
        queryset = CourseEnrolment.objects.all()
        user = self.request.user
        if user.is_staff:
            return queryset
        if user.is_dive_officer():
            return queryset.filter(user__club=user.club)
        return queryset.filter(user=user)

    def create(self, request):
        user = self.request.user
        data = request.data

        # Admins can create an enrolment for any user
        if user.is_staff:
            return super(CourseEnrolmentViewSet, self).create(request)

        # DOs can create an enrolment for members of their club
        if user.is_dive_officer():
            queryset = User.objects.filter(club=user.club)
            target_user = get_object_or_404(queryset, pk=request.data['user'])
            return super(CourseEnrolmentViewSet, self).create(request)

        # Users can create an enrolment for themselves
        target_user = get_object_or_404(User, pk=request.data['user'])
        if target_user == user:
            return super(CourseEnrolmentViewSet, self).create(request)
        raise PermissionDenied

    def list(self, request, course_pk=None):
        # Bare lists are not allowed; clients must make nested requests
        if course_pk is None:
            raise MethodNotAllowed(self.action)

        # Otherwise, filter on the course PK and return the results
        course = get_object_or_404(Course, pk=course_pk)
        queryset = self.get_queryset().filter(course=course)
        serializer = CourseEnrolmentSerializer(queryset, many=True)
        return Response(serializer.data)


class CourseInstructionViewSet(PermissionClassesByActionMixin, viewsets.ModelViewSet):

    queryset = CourseInstruction.objects.all()
    # Admins, DOs, and course organizers can view the instructor lists for
    # courses
    permission_classes = [
        C(IsAdminUser) | C(IsDiveOfficer) | C(IsCourseOrganizer) | C(IsUser)
    ]
    serializer_class = CourseInstructionSerializer

    def get_queryset(self):
        queryset = CourseInstruction.objects.all()
        user = self.request.user
        if user.is_staff:
            return queryset
        if user.is_dive_officer():
            return queryset.filter(user__club=user.club)
        return queryset.filter(user=user)

    def list(self, request, course_pk=None):
        if course_pk is None:
            raise MethodNotAllowed(self.action)
        queryset = self.get_queryset().filter(course__pk=course_pk)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


    def create(self, request, course_pk=None):
        # Creation is only available through nested router
        if course_pk is None:
            raise MethodNotAllowed(self.action)
        course = get_object_or_404(Course, pk=course_pk)
        user = get_object_or_404(User, pk=request.data.get('user', None))
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(
            course=course,
            user=user
        )
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class CertificateViewSet(viewsets.ModelViewSet):

    queryset = Certificate.objects.all()
    serializer_class = CertificateSerializer
