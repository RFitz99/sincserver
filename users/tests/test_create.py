from django.core.urlresolvers import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from clubs.models import Club
from users.models import User
from users.tests.shared import MOCK_USER_DATA

###############################################################################
# These tests check our assumptions about how users are created.
###############################################################################

class UserCreationTestCase(APITestCase):

    def setUp(self):
        # Create a club and a Dive Officer
        self.club = Club.objects.create(name='UCCSAC')
        self.do = User.objects.create_user(first_name='Dave', last_name='Officer')
        self.do.club = self.club
        self.do.save()
        self.do.become_dive_officer()

    ###########################################################################
    # Administrators and DOs can create users; these requests
    # should succeed.
    ###########################################################################

    def test_dive_officers_can_create_users(self):
        self.client.force_authenticate(self.do)
        result = self.client.post(reverse('user-list'), MOCK_USER_DATA)
        self.assertEqual(result.status_code, status.HTTP_201_CREATED)

    def test_admins_can_create_users(self):
        staff = User.objects.create_user(first_name='Staff', last_name='Member')
        staff.is_staff = True
        staff.save()
        self.client.force_authenticate(staff)
        result = self.client.post(reverse('user-list'), MOCK_USER_DATA)
        self.assertEqual(result.status_code, status.HTTP_201_CREATED)

    ###########################################################################
    # Unauthenticated users and regular users who aren't DOs cannot
    # create users; these requests should fail.
    ###########################################################################

    def test_unauthenticated_users_cannot_create_users(self):
        result = self.client.post(reverse('user-list'), MOCK_USER_DATA)
        self.assertEqual(result.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_regular_users_cannot_create_users(self):
        u = User.objects.create_user(first_name='Normal', last_name='User', club=self.club)
        self.client.force_authenticate(u)
        result = self.client.post(reverse('user-list'), MOCK_USER_DATA)
        self.assertEqual(result.status_code, status.HTTP_403_FORBIDDEN)

    ###########################################################################
    # When DOs create a user, the new user's 'club' field should be set
    # to the DO's club. It is not required for the request to set the
    # club field, and it should be ignored.
    # 
    # Administrators can set the new user's club when creating them,
    # or leave it blank.
    ###########################################################################

    def test_creating_a_user_adds_that_user_to_a_club(self):
        self.client.force_authenticate(self.do)
        result = self.client.post(reverse('user-list'), MOCK_USER_DATA)
        self.assertEqual(result.status_code, status.HTTP_201_CREATED)
        u = User.objects.get(first_name='Joe', last_name='Bloggs')
        self.assertEqual(u.club, self.club)

    def test_superusers_can_set_club_field(self):
        su = User.objects.create_superuser(first_name='Super', last_name='User', password='password')
        dauntsac = Club.objects.create(name='Daunt SAC')
        self.client.force_authenticate(su)
        data = MOCK_USER_DATA.copy()
        data['club'] = dauntsac.id
        result = self.client.post(reverse('user-list'), data)
        self.assertEqual(result.status_code, status.HTTP_201_CREATED)
        u = User.objects.get(first_name='Joe')
        self.assertEqual(u.club, dauntsac)

    def test_dive_officers_cannot_set_club_field(self):
        self.client.force_authenticate(self.do)
        dauntsac = Club.objects.create(name='Daunt SAC')
        data = MOCK_USER_DATA.copy()
        data['club'] = dauntsac.id
        result = self.client.post(reverse('user-list'), data)
        self.assertEqual(result.status_code, status.HTTP_201_CREATED)
        u = User.objects.get(first_name='Joe')
        self.assertEqual(u.club, self.do.club)

    ###########################################################################
    # Users log in with their CFT number and their password, so we
    # automatically set the Django username during user creation. If
    # a 'username' field is supplied in the request data, it's ignored.
    ###########################################################################

    def test_new_users_will_have_their_id_as_their_username(self):
        self.client.force_authenticate(self.do)
        response = self.client.post(reverse('user-list'), MOCK_USER_DATA)
        user = User.objects.get(first_name=MOCK_USER_DATA['first_name'])
        self.assertEqual(user.username, str(user.id))

    def test_username_field_in_request_is_ignored(self):
        data = MOCK_USER_DATA.copy()
        data['username'] = 'bogus_username'
        self.client.force_authenticate(self.do)
        response = self.client.post(reverse('user-list'), MOCK_USER_DATA)
        user = User.objects.get(first_name=MOCK_USER_DATA['first_name'])
        self.assertEqual(user.username, str(user.id))
