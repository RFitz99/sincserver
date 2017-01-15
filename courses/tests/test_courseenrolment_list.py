from django.core.urlresolvers import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from clubs.models import Club
from courses.models import Course, CourseEnrolment
from qualifications.models import Certificate
from users.models import User

###############################################################################
# The API should not expose a list of all course enrolments: it would be
# huge, and not very useful. Instead, clients should access course enrolments
# by course.
###############################################################################


class CourseEnrolmentListTestCase(APITestCase):
    def setUp(self):
        # Create a certificate for a course
        certificate = Certificate.objects.create(name='Trainee Diver')
        # Create course creator and organizer
        self.club = Club.objects.create(name='UCCSAC')
        self.creator = User.objects.create_user('Course', 'Creator', club=self.club)
        self.organizer = User.objects.create_user('Course', 'Organizer', club=self.club)
        # Create a course
        self.course = Course.objects.create(
            certificate=certificate,
            creator=self.creator,
            organizer=self.organizer
        )
        # Create a user who will try to join/leave courses
        self.user = User.objects.create_user('Normal', 'User', club=self.club)
        # Create a DO who will have list privs
        self.do = User.objects.create_user('Dive', 'Officer', club=self.club)
        self.do.become_dive_officer()
        # Create a user from a different club
        self.other_user = User.objects.create_user('Other', 'User', club=self.club)


    def test_admins_cannot_list_courseenrolments(self):
        admin = User.objects.create_user('Staff', 'Member', is_staff=True)
        self.client.force_authenticate(admin)
        response = self.client.get(reverse('courseenrolment-list'))
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED,
                         'Admins shouldn\'t be able to list all courseenrolments'
                        )

    def test_unauthenticated_users_cannot_list_courseenrolments(self):
        response = self.client.get(reverse('courseenrolment-list'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED,
                         'Admins shouldn\'t be able to list all courseenrolments'
                        )

    def test_users_cannot_list_courseenrolments(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse('courseenrolment-list'))
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED,
                         'Users shouldn\'t be able to list all courseenrolments'
                        )

    def test_dos_cannot_list_courseenrolments(self):
        self.client.force_authenticate(self.do)
        response = self.client.get(reverse('courseenrolment-list'))
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED,
                         'DOs shouldn\'t be able to list all courseenrolments'
                        )
