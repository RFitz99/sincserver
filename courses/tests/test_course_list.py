from django.core.urlresolvers import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from clubs.models import Club
from courses.models import Course, CourseEnrolment
from qualifications.models import Certificate
from users.models import User

class CourseListTestCase(APITestCase):

    def setUp(self):
        # Create a certificate
        cert = Certificate.objects.create(name='Trainee Diver')
        # Create a course and its creator and organizer
        self.creator = User.objects.create_user('Course', 'Creator')
        self.organizer = User.objects.create_user('Course', 'Organizer')
        # Create a user
        self.user = User.objects.create_user('Normal', 'User')

    def test_unauthenticated_user_cannot_list_courses(self):
        response = self.client.get(reverse('course-list'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_user_can_list_courses(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse('course-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
