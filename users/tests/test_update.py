from django.core.urlresolvers import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from clubs.models import Club
from users.models import User
from users.tests.shared import MOCK_USER_DATA

###############################################################################
# These tests check our assumptions about how users are created.
###############################################################################

UPDATE_DATA = {
    'first_name': 'Bill',
    'last_name': 'Blow',
    'email': 'bill@example.com',
}

class UserUpdateTestCase(APITestCase):

    def setUp(self):
        self.club = Club.objects.create(name='UCC')
        self.do = User.objects.create_user('Dave', 'Officer', club=self.club)
        self.do.become_dive_officer()
        self.member = User.objects.create_user('Joe', 'Bloggs', club=self.club)
        # Create another club
        self.csac = Club.objects.create(name='CSAC')
        self.other_member = User.objects.create_user('Other', 'Member', club=self.csac)

    def test_dive_officers_can_update_their_members(self):
        self.client.force_authenticate(self.do)
        response = self.client.put(reverse('user-detail', args=[self.member.id]), UPDATE_DATA)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # This throws a 404, because members of another club aren't even in the queryset
    # to start with. (This may change in the future.)
    def test_dive_officers_cannot_update_members_of_other_clubs(self):
        self.client.force_authenticate(self.do)
        response = self.client.put(reverse('user-detail', args=[self.other_member.id]), UPDATE_DATA)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_admins_can_update_members(self):
        staff = User.objects.create_user('Staff', 'Member', is_staff=True)
        self.client.force_authenticate(staff)
        response = self.client.put(reverse('user-detail', args=[self.member.id]), UPDATE_DATA)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_users_can_update_their_own_profile(self):
        self.client.force_authenticate(self.member)
        response = self.client.put(reverse('user-detail', args=[self.member.id]), UPDATE_DATA)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
