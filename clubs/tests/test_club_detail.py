from django.core.urlresolvers import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from clubs.models import Club, Region
from clubs.views import ClubViewSet
from users.models import User

class ClubDetailTestCase(APITestCase):

    # When user lists are returned as part of a club detail, we expect
    # all of these fields (and no others) to be present.
    expected_member_fields = ['id', 'first_name', 'last_name', 'email',]

    def setUp(self):
        # Create a club that we'll try to update
        self.club = Club.objects.create(name='UCC')
        self.do = User.objects.create_user(first_name='Dave', last_name='Officer', club=self.club)
        self.do.become_dive_officer()
        self.member = User.objects.create_user(first_name='Normal', last_name='User', club=self.club)
        self.staff = User.objects.create_user('Staff', 'Member', is_staff=True)
        # A club that nobody is a member of
        self.csac = Club.objects.create(name='Cork')

    ###########################################################################
    # Admins can view club details, and can see all the fields defined
    # in ClubViewSet.admin_fields
    ###########################################################################

    def test_admin_can_view_club_detail(self):
        self.client.force_authenticate(self.staff)
        response = self.client.get(reverse('club-detail', args=[self.club.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_admin_sees_all_expected_fields(self):
        self.client.force_authenticate(self.staff)
        response = self.client.get(reverse('club-detail', args=[self.club.id]))
        data = response.data
        expected_fields = ClubViewSet.admin_fields
        returned_fields = [field for field in data]
        for expected_field in expected_fields:
            self.assertIn(expected_field, returned_fields,
                          'Admin should see field "{}"'.format(expected_field))

    def test_admin_sees_no_unexpected_fields(self):
        self.client.force_authenticate(self.staff)
        response = self.client.get(reverse('club-detail', args=[self.club.id]))
        data = response.data
        expected_fields = ClubViewSet.admin_fields
        returned_fields = [field for field in data]
        for returned_field in returned_fields:
            self.assertIn(returned_field, expected_fields,
                          'Admin shouldn\'t see field "{}"'.format(returned_field))

    ###########################################################################
    # Users can view club details, and can see all the fields defined
    # in ClubViewSet.base_fields
    ###########################################################################

    def test_member_can_view_own_club_detail(self):
        self.client.force_authenticate(self.member)
        response = self.client.get(reverse('club-detail', args=[self.club.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_member_sees_all_expected_fields_for_own_club(self):
        self.client.force_authenticate(self.member)
        response = self.client.get(reverse('club-detail', args=[self.club.id]))
        data = response.data
        expected_fields = ClubViewSet.base_fields
        returned_fields = [field for field in data]
        for expected_field in expected_fields:
            self.assertIn(expected_field, returned_fields,
                          'User should see field "{}" when viewing their club'.format(expected_field))

    def test_member_sees_no_unexpected_fields_for_own_club(self):
        self.client.force_authenticate(self.member)
        response = self.client.get(reverse('club-detail', args=[self.club.id]))
        data = response.data
        expected_fields = ClubViewSet.base_fields
        returned_fields = [field for field in data]
        for returned_field in returned_fields:
            self.assertIn(returned_field, expected_fields,
                          'User shouldn\'t see field "{}" when viewing their club'.format(returned_field))

    def test_member_can_view_other_club_detail(self):
        self.client.force_authenticate(self.member)
        response = self.client.get(reverse('club-detail', args=[self.csac.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_member_sees_all_expected_fields_for_other_club(self):
        self.client.force_authenticate(self.member)
        response = self.client.get(reverse('club-detail', args=[self.csac.id]))
        data = response.data
        expected_fields = ClubViewSet.base_fields
        returned_fields = [field for field in data]
        for expected_field in expected_fields:
            self.assertIn(expected_field, returned_fields,
                          'User should see field "{}" when viewing another club'.format(expected_field))

    def test_member_sees_no_unexpected_fields_for_other_club(self):
        self.client.force_authenticate(self.member)
        response = self.client.get(reverse('club-detail', args=[self.csac.id]))
        data = response.data
        expected_fields = ClubViewSet.base_fields
        returned_fields = [field for field in data]
        for returned_field in returned_fields:
            self.assertIn(returned_field, expected_fields,
                          'User shouldn\'t see field "{}" when viewing another club'.format(returned_field))

    ###########################################################################
    # DOs can see more fields than ordinary members when viewing their
    # own club, but they don't have any special privileges over other
    # clubs.
    ###########################################################################

    def test_do_can_view_own_club_detail_of_own_club(self):
        self.client.force_authenticate(self.do)
        response = self.client.get(reverse('club-detail', args=[self.club.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_do_sees_all_expected_fields_for_member_data(self):
        self.client.force_authenticate(self.do)
        response = self.client.get(reverse('club-detail', args=[self.club.id]))
        data = response.data
        for user in data['users']:
            returned_fields = [k for k in user]
            for field in self.expected_member_fields:
                self.assertIn(field, returned_fields,
                              'DO should see field "{}" in member data'.format(field))

    def test_do_sees_no_unexpected_fields_in_member_data(self):
        self.client.force_authenticate(self.do)
        response = self.client.get(reverse('club-detail', args=[self.club.id]))
        data = response.data
        for user in data['users']:
            returned_fields = [k for k in user]
            for field in returned_fields:
                self.assertIn(field, self.expected_member_fields,
                              'DO shouldn\'t see field "{}" in member data'.format(field))

    def test_do_receives_list_of_members(self):
        self.client.force_authenticate(self.do)
        response = self.client.get(reverse('club-detail', args=[self.club.id]))
        data = response.data
        # Check the, presence, length and shape of the data returned
        self.assertIn('users', [k for k in data],
                     'DO should see a list of members in club detail')
        expected_member_length = 2 # DO and member
        self.assertEqual(len(data['users']), expected_member_length)
