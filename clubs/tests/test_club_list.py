from django.core.urlresolvers import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from clubs.models import Club, Region
from users.models import User

class ClubViewTestCase(APITestCase):

    def setUp(self):
        # Create a club that we'll try to update
        self.club = Club.objects.create(name='UCC')

    ###########################################################################
    # Administrators, RDOs, and DOs can view club lists.
    ###########################################################################

    def test_admin_can_list_clubs(self):
        su = User.objects.create_superuser(first_name='Super', last_name='User', password='password')
        self.client.force_authenticate(su)
        response = self.client.get(reverse('club-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # We expect the length of the list returned to be 1
        result = response.data
        expected_length = 1
        self.assertEqual(len(result), expected_length)

    def test_do_can_list_clubs(self):
        do = User.objects.create_user(first_name='Dave', last_name='Officer', club=self.club)
        do.become_dive_officer()
        self.client.force_authenticate(do)
        response = self.client.get(reverse('club-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # We expect the length of the list returned to be 1
        result = response.data
        expected_length = 1
        self.assertEqual(len(result), expected_length)

    ###########################################################################
    # Unauthenticated and regular users cannot view club lists.
    ###########################################################################

    def test_unauthenticated_user_cannot_list_clubs(self):
        response = self.client.get(reverse('club-list'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_cannot_list_clubs(self):
        member = User.objects.create_user(first_name='Normal', last_name='User', club=self.club)
        self.client.force_authenticate(member)
        response = self.client.get(reverse('club-list'))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
