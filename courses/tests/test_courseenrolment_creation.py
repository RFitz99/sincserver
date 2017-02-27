from django.core.urlresolvers import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from clubs.models import Club
from courses.models import Course, CourseEnrolment
from qualifications.models import Certificate
from users.models import User

###############################################################################
# These tests check our assumptions about who can and cannot enrol
# users on courses
###############################################################################

class CourseEnrolmentCreationCase(APITestCase):
    def setUp(self):
        # Create a certificate
        certificate = Certificate.objects.create(name='Trainee Diver')
        # Create course creator and organizer
        self.club = Club.objects.create(name='UCCSAC')
        self.creator = User.objects.create_user('Course', 'Creator', club=self.club)
        self.organizer = User.objects.create_user('Course', 'Organizer', club=self.club)
        self.course = Course.objects.create(
            certificate=certificate,
            creator=self.creator,
            organizer=self.organizer
        )
        # Create a user who will try to join/leave courses
        self.user = User.objects.create_user('Normal', 'User', club=self.club)
        # Create a DO who will have enrol privs
        self.do = User.objects.create_user('Dive', 'Officer', club=self.club)
        self.do.become_dive_officer()
        # Create a user from a different club
        self.other_user = User.objects.create_user('Other', 'User')

    ###########################################################################
    # Unauthenticated users can't enrol users
    ###########################################################################

    def test_unauthenticated_user_cannot_enrol_a_user_on_course(self):
        post_data = {'user': self.user.id, 'course': self.course.id}
        response = self.client.post(reverse('courseenrolment-list'), post_data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED,
                         'Unauthenticated users should not be able to enrol users on courses'
                        )

    ###########################################################################
    # Regular users can enrol themselves, but not other users
    ###########################################################################

    def test_user_can_add_themselves_to_course(self):
        self.client.force_authenticate(self.user)
        post_data = {'user': self.user.id, 'course': self.course.id}
        response = self.client.post(reverse('courseenrolment-list'), post_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED,
                         'Users should be able to enrol themselves on courses'
                        )

    def test_user_cannot_add_another_user_to_course(self):
        self.client.force_authenticate(self.user)
        post_data = {'user': self.other_user.id, 'course': self.course.id}
        response = self.client.post(reverse('courseenrolment-list'), post_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN,
                         'Users should not be able to enrol other users on courses'
                        )

    ###########################################################################
    # Dive Officers can enrol users from their club, but not users from
    # other clubs
    ###########################################################################

    def test_dive_officer_can_enrol_user_in_same_club(self):
        self.client.force_authenticate(self.do)
        post_data = {'user': self.user.id, 'course': self.course.id}
        response = self.client.post(reverse('courseenrolment-list'), post_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED,
                         'DOs should be able to enrol their club\'s members on courses'
                        )

    def test_dive_officer_cannot_enrol_user_from_other_club(self):
        self.client.force_authenticate(self.do)
        post_data = {'user': self.other_user.id, 'course': self.course.id}
        response = self.client.post(reverse('courseenrolment-list'), post_data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND,
                         'DOs should not be able to enrol other clubs\' members on courses'
                        )


    ###########################################################################
    # Administrators can enrol any user on a course
    ###########################################################################

    def test_admin_can_enrol_user(self):
        admin = User.objects.create_user('Staff', 'Member', is_staff=True)
        self.client.force_authenticate(admin)
        post_data = {'user': self.user.id, 'course': self.course.id}
        response = self.client.post(reverse('courseenrolment-list'), post_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED,
                        'Admins should be able to enrol any member on a course')
