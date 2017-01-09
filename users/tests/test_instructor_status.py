from django.core.urlresolvers import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from clubs.models import Club
from qualifications.models import Certificate
from users.models import User
from users.tests.shared import MOCK_USER_DATA

class CheckInstructorStatusTestCase(APITestCase):

    def setUp(self):
        # Create an instructor
        self.u = User.objects.create_user(first_name='Joe', last_name='Bloggs')
        self.club = Club.objects.create(name='UCCSAC')
        self.u.club = self.club
        self.club.save()
        self.mon1 = Certificate.objects.create(name='Mon 1', is_instructor_certificate=True)
        self.u.receive_certificate(self.mon1)

        # Create a non-instructor
        self.u2 = User.objects.create_user(first_name='Bob', last_name='Pleb')

        # Create a non-instructor DO
        self.do = User.objects.create_user(first_name='Dave', last_name='Officer')
        self.do.club = self.club
        self.do.become_dive_officer()
        self.do.save()

    def test_is_instructor_returns_true_when_it_should(self):
        self.assertTrue(self.u.is_instructor())

    def test_is_instructor_returns_false_when_it_should(self):
        self.assertFalse(self.u2.is_instructor())

    def test_querying_instructor_list_returns_expected_result(self):
        self.client.force_authenticate(self.do)
        result = self.client.get(reverse('user-active-instructors'))
        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.assertEqual(len(result.data), 1)
