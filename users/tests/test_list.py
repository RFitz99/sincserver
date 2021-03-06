from django.core.urlresolvers import reverse
from faker import Faker

from rest_framework import status
from rest_framework.test import APITestCase

from clubs.models import Club
from users.models import User
from users.tests.shared import MOCK_USER_DATA

UCCSAC_SIZE = 10
CSAC_SIZE = 10

class UserListTestCase(APITestCase):

    def setUp(self):
        fake = Faker()
        # Create an admin
        self.admin = User.objects.create_user('Staff', 'Member', is_staff=True)
        # Create a club with a DO and UCCSAC_SIZE members
        self.uccsac = Club.objects.create(name='UCCSAC')
        self.do = User.objects.create_user('Dave', 'Officer', club=self.uccsac)
        self.do.become_dive_officer()
        for i in range(UCCSAC_SIZE-1):
            User.objects.create_user(fake.first_name(), fake.last_name(), club=self.uccsac)
        # Create a second club, with more members
        self.csac = Club.objects.create(name='CSAC')
        for i in range(CSAC_SIZE):
            User.objects.create_user(fake.first_name(), fake.last_name(), club=self.csac)

    ###########################################################################
    # Administrators and Dive Officers can view lists of users. Dive
    # Officers cannot list the members of other clubs.
    ###########################################################################

    def test_administrators_can_list_all_users(self):
        self.client.force_authenticate(self.admin)
        response = self.client.get(reverse('user-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # The result should include the admin.
        expected_length = UCCSAC_SIZE + CSAC_SIZE + 1
        self.assertEqual(len(response.data), expected_length)

    def test_dive_officers_can_list_their_club_members(self):
        self.client.force_authenticate(self.do)
        response = self.client.get(reverse('user-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_length = UCCSAC_SIZE
        self.assertEqual(len(response.data), expected_length)

    def test_administrators_can_filter_by_club(self):
        self.client.force_authenticate(self.admin)
        response = self.client.get(reverse('club-users-list', args=[self.uccsac.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), UCCSAC_SIZE)

    def test_dive_officers_can_filter_by_their_own_club(self):
        self.client.force_authenticate(self.do)
        response = self.client.get(reverse('club-users-list', args=[self.uccsac.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), UCCSAC_SIZE)

    # This request doesn't actually fail; it just returns a list of
    # length 0.
    def test_dive_officers_cannot_filter_by_other_clubs(self):
        self.client.force_authenticate(self.do)
        response = self.client.get(reverse('club-users-list', args=[self.csac.id]))
        self.assertEqual(len(response.data), 0)

    ###########################################################################
    # Unauthenticated and regular users can't view lists of users.
    ###########################################################################

    def test_unauthenticated_users_cannot_list_all_users(self):
        response = self.client.get(reverse('user-list'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_regular_users_cannot_list_all_users(self):
        # Pick a member of UCCSAC who is not the DO
        u = User.objects.filter(club=self.uccsac).exclude(id=self.do.id)[0]
        self.client.force_authenticate(u)
        response = self.client.get(reverse('user-list'))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


    ###########################################################################
    # A special list method is '/users/me': Every authenticated user may
    # view their own profile.
    ###########################################################################

    def test_authenticated_users_can_view_their_profile(self):
        self.client.force_authenticate(self.do)
        response = self.client.get(reverse('user-me'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class UserFilterListTestCase(APITestCase):

    def setUp(self):
        fake = Faker()
        # Create an admin
        self.admin = User.objects.create_user('Staff', 'Member', is_staff=True)
        # Create a club with a DO and a member
        self.uccsac = Club.objects.create(name='UCCSAC')
        self.do = User.objects.create_user('Dave', 'Officer', club=self.uccsac)
        self.do.become_dive_officer()
        self.member = User.objects.create_user('Club', 'Member', club=self.uccsac)

    def test_admin_can_filter_by_name_fragment(self):
        self.client.force_authenticate(self.admin)
        data = {'name': 'ffic'}
        response = self.client.get('{}?name={}'.format(reverse('user-list'), data['name']))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_admin_can_filter_by_id(self):
        uid = User.objects.get(first_name='Club', last_name='Member').id
        self.client.force_authenticate(self.admin)
        response = self.client.get('{}?name={}'.format(reverse('user-list'), uid))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_filtering_looks_at_both_first_and_last_names(self):
        User.objects.create_user('Officer', 'Friendly', club=self.uccsac)
        self.client.force_authenticate(self.admin)
        data = {'name': 'ffic'}
        response = self.client.get('{}?name={}'.format(reverse('user-list'), data['name']))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_filtering_is_case_insensitive(self):
        User.objects.create_user('Ffion', 'Jones', club=self.uccsac)
        self.client.force_authenticate(self.admin)
        data = {'name': 'ffi'}
        response = self.client.get('{}?name={}'.format(reverse('user-list'), data['name']))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_empty_querystring_returns_full_list(self):
        self.client.force_authenticate(self.admin)
        response = self.client.get('{}?name={}'.format(reverse('user-list'), ''))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_dive_officer_can_search_only_within_club(self):
        self.client.force_authenticate(self.do)
        response = self.client.get('{}?name={}'.format(reverse('user-list'), 'member'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_unauthenticated_users_cannot_search(self):
        response = self.client.get('{}?name={}'.format(reverse('user-list'), 'member'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_users_cannot_search(self):
        self.client.force_authenticate(self.member)
        response = self.client.get('{}?name={}'.format(reverse('user-list'), 'member'))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
