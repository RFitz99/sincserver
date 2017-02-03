from django.core.urlresolvers import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from clubs.models import Club
from courses.models import Course, CourseInstruction
from qualifications.models import Certificate, Qualification
from users.models import User

class UserCoursesTestCase(APITestCase):
    def setUp(self):
        self.staff = User.objects.create_user('Staff', 'Member', is_staff=True)
        club = Club.objects.create(name='UCC')
        self.member = User.objects.create_user('Club', 'Member', club=club)
        cert = Certificate.objects.create(name='Trainee Diver')
        course = Course.objects.create(
          certificate=cert,
          creator=self.staff,
          organizer=self.member,
        )
        CourseInstruction.objects.create(user=self.member, course=course)

    def test_user_can_view_own_courses_organized(self):
        self.client.force_authenticate(self.member)
        response = self.client.get(reverse('user-courses-organized', args=[self.member.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_user_can_view_own_courses_taught(self):
        self.client.force_authenticate(self.member)
        response = self.client.get(reverse('user-courses-taught', args=[self.member.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
