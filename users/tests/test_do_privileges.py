from django.core.urlresolvers import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from clubs.models import Club
from qualifications.models import Certificate, Qualification
from users.models import User
from users.tests.shared import MOCK_USER_DATA

class DiveOfficerPrivilegesTestCase(APITestCase):

    def setUp(self):
        # Create a club and its dive officer
        self.club = Club.objects.create(name='UCCSAC')
        self.do = User.objects.create_user(first_name='Dave', last_name='Officer')
        self.do.club = self.club
        self.do.save()
        self.do.become_dive_officer()
        # Create another member for this club
        User.objects.create_user('Other', 'Member', club=self.club)
        # Create another club with one member
        self.club2 = Club.objects.create(name='UCDSAC')
        self.other_user = User.objects.create_user(first_name='Other', last_name='User')
        self.other_user.club = self.club2
        self.other_user.save()

    def test_do_can_retrieve_user_list(self):
        # Log in
        self.client.force_authenticate(self.do)
        # Retrieve a list of all users
        result = self.client.get(reverse('user-list'))
        self.assertEqual(result.status_code, status.HTTP_200_OK) # Should return 200 OK
        expected_length = 2 # i.e., the DO and the other member from the same club
        self.assertEqual(len(result.data), 2) 

    def test_do_can_create_users(self):
        self.client.force_authenticate(self.do)
        result = self.client.post(reverse('user-list'), MOCK_USER_DATA)
        self.assertEqual(result.status_code, status.HTTP_201_CREATED)
        # Check the DB: is the new user in there?
        self.assertTrue(
            User.objects.filter(first_name=MOCK_USER_DATA['first_name'],
                                last_name=MOCK_USER_DATA['last_name']
                               ).exists()
        )

    def test_regular_user_cannot_create_users(self):
        self.client.force_authenticate(self.other_user)
        result = self.client.post(reverse('user-list'), MOCK_USER_DATA)
        self.assertEqual(result.status_code, status.HTTP_403_FORBIDDEN)
        # Confirm that the new user isn't in the database
        self.assertFalse(
            User.objects.filter(first_name=MOCK_USER_DATA['first_name'],
                                last_name=MOCK_USER_DATA['last_name']
                               ).exists()
        )

    def test_dive_officer_can_view_club_qualifications(self):
        d1 = Certificate.objects.create(name='Trainee Diver')
        self.client.force_authenticate(self.do)
        bob = User.objects.create_user(first_name='Bob', last_name='Smith', club=self.do.club)
        bob_d1 = Qualification.objects.create(user=bob, certificate=d1)
        result = self.client.get(reverse('club-qualifications', args=[self.do.club.id]))
        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.assertEqual(len(result.data), 1)
