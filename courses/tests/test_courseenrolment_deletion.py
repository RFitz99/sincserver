from django.core.urlresolvers import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from clubs.models import Club
from courses.models import Course, CourseEnrolment
from qualifications.models import Certificate
from users.models import User

class CourseEnrolmentDeletionTestCase(APITestCase):
    def setUp(self):
        # Create a course
        certificate = Certificate.objects.create(name='Trainee Diver')
        creator = User.objects.create_user('Course', 'Creator')
        organizer = User.objects.create_user('Course', 'Organizer')
        self.course = Course.objects.create(
            certificate=certificate,
            creator=creator,
            organizer=organizer
        )
        # Create a club
        club = Club.objects.create(name='UCCSAC')
        # Create a user
        self.user = User.objects.create_user('Normal', 'User', club=club)
        # Enrol the user
        self.enrolment = CourseEnrolment.objects.create(user=self.user, course=self.course)
        # Create a DO who will have withdrawal privs
        self.do = User.objects.create_user('Dive', 'Officer', club=club)
        self.do.become_dive_officer()
        # Create a user from a different club
        self.other_user = User.objects.create_user('Other', 'User')

    def test_unauthenticated_user_cannot_remove_another_user_from_course(self):
        response = self.client.delete(reverse('courseenrolment-detail', args=[self.enrolment.id]))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED,
                         'Unauthenticated users shouldn\'t be able to remove users from courses'
                        )

    def test_user_can_withdraw_from_course(self):
        self.client.force_authenticate(self.user)
        response = self.client.delete(reverse('courseenrolment-detail', args=[self.enrolment.id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT,
                        'Users should be able to withdraw from courses'
                        )

    def test_user_cannot_remove_another_user_from_course(self):
        self.client.force_authenticate(self.user)
        other_enrolment = CourseEnrolment.objects.create(user=self.other_user, course=self.course)
        response = self.client.delete(reverse('courseenrolment-detail', args=[other_enrolment.id]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND,
                         'Users should not be able to remove other users from courses'
                        )
    
    def test_dive_officer_can_withdraw_user_in_same_club(self):
        self.client.force_authenticate(self.do)
        response = self.client.delete(reverse('courseenrolment-detail', args=[self.enrolment.id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT,
                         'DOs should be able to withdraw their club\'s members from courses'
                        )

    def test_dive_officer_cannot_withdraw_user_from_other_club(self):
        self.client.force_authenticate(self.do)
        other_enrolment = CourseEnrolment.objects.create(user=self.other_user, course=self.course)
        response = self.client.delete(reverse('courseenrolment-detail', args=[other_enrolment.id]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND,
                         'DOs shouldn\'t be able to withdraw other clubs\' members from courses'
                        )

    def test_admin_can_withdraw_user(self):
        admin = User.objects.create_user('Staff', 'Member', is_staff=True)
        self.client.force_authenticate(admin)
        response = self.client.delete(reverse('courseenrolment-detail', args=[self.enrolment.id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT,
                         'Admins should be able to remove users from courses'
                        )
