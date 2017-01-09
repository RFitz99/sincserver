from django.core.urlresolvers import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from clubs.models import Club
from users.models import User

class ClubViewTestCase(APITestCase):

    def setUp(self):
        # Create a club that we'll try to update
        self.club = Club.objects.create(name='UCC')

    def test_unauthenticated_users_cannot_view_list(self):
        response = self.client.get(reverse('club-list'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_admins_can_view_list(self):
        su = User.objects.create_superuser(first_name='Super', last_name='User', password='password')
        self.client.force_authenticate(su)
        response = self.client.get(reverse('club-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # We expect the length of the list returned to be 1
        result = response.data
        expected_length = 1
        self.assertEqual(len(result), expected_length)

    def test_dos_can_view_list(self):
        do = User.objects.create_user(first_name='Dave', last_name='Officer', club=self.club)
        do.become_dive_officer()
        self.client.force_authenticate(do)
        response = self.client.get(reverse('club-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # We expect the length of the list returned to be 1
        result = response.data
        expected_length = 1
        self.assertEqual(len(result), expected_length)

    def test_do_can_view_detail_of_own_club(self):
        do = User.objects.create_user(first_name='Dave', last_name='Officer', club=self.club)
        do.become_dive_officer()
        self.client.force_authenticate(do)
