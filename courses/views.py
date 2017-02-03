from django.shortcuts import get_object_or_404
from rest_condition import C
from rest_framework import viewsets
from rest_framework.exceptions import MethodNotAllowed, PermissionDenied
from rest_framework.mixins import CreateModelMixin, DestroyModelMixin, RetrieveModelMixin, UpdateModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from courses.models import Certificate, Course, CourseEnrolment, CourseInstruction
from courses.serializers import CertificateSerializer, CourseSerializer, CourseEnrolmentSerializer, CourseInstructionSerializer
from mixins import PermissionClassesByActionMixin
from permissions.permissions import IsAdminUser, IsDiveOfficer, IsSafeMethod, IsSameUser, IsUser
from users.models import User

class CourseViewSet(viewsets.ModelViewSet):

    queryset = Course.objects.all()
    serializer_class = CourseSerializer

    permission_classes = (C(IsAdminUser) | C(IsSafeMethod),)

    permission_classes_by_action = {
        'create': [C(IsAdminUser) | C(IsDiveOfficer)],
    }

    def get_permissions(self):
        try:
            return ([IsAuthenticated()]
                    + [permission() for permission in self.permission_classes_by_action[self.action]])
        except KeyError:
            return ([IsAuthenticated()]
                    + [permission() for permission in self.permission_classes])

    def perform_create(self, serializer):
        user = self.request.user
        # When a non-admin creates a course, we'll set them as the
        # creator and the organizer by default.
        creator = user
        organizer = user
        region = user.club.region

        # If the user is an administrator, they can override the default creator
        if user.is_staff and ('creator' in self.request.data):
            creator = User.objects.get(pk=self.request.data['creator'])

        # If the user is an admin or Dive Officer, they can
        # override the default organizer. An admin can set this to
        # any user they like, but a Dive Officer can only set the
        # organizer to a member of their own club.
        #
        # We will set the region to the organizer's region by default,
        # unless the user explicitly sets the region (handled later).
        if (user.is_staff or user.is_dive_officer()) and 'organizer' in self.request.data:
            try:
                proposed_organizer = User.objects.get(pk=self.request.data['organizer'])
                # Staff members may set any user as organizer; DOs may only set members
                # of their own club
                if user.is_staff or proposed_organizer.club == user.club:
                    organizer = proposed_organizer
            except User.DoesNotExist:
                # Fall back to setting the requesting user as the organizer
                organizer = user

        # If the user is an admin, they can override the default region.
        if user.is_staff and ('region' in self.request.data):
            # TODO: Implement this!
            pass

        # Find the certificate by its ID
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


    def list(self, request, region_pk=None):
        # If the request contains a region ID, then filter the
        # queryset to return only courses from that region.
        queryset = Course.objects.all()
        if region_pk is not None:
            queryset = queryset.filter(region=region_pk)
        serializer = CourseSerializer(queryset, many=True)
        return Response(serializer.data)


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
    serializer_class = CourseInstructionSerializer

    def get_queryset(self):
        queryset = CourseInstruction.objects.all()
        user = self.request.user
        if user.is_staff:
            return queryset
        if user.is_dive_officer():
            return queryset.filter(user__club=user.club)
        return queryset.filter(user=user)

    permission_classes_by_action = {
    }


class CertificateViewSet(viewsets.ModelViewSet):

    queryset = Certificate.objects.all()
    serializer_class = CertificateSerializer
