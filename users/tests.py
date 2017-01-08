from django.core.urlresolvers import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APITestCase

from clubs.models import Club
from qualifications.models import Certificate, Qualification
from users.models import User

MOCK_USER_DATA = {
        'first_name': 'Joe',
        'last_name': 'Bloggs',
        'email': 'joe_bloggs@example.com'
        }

class SimpleUserTestCase(APITestCase):

    def setUp(self):
        self.u = User.objects.create_user(first_name='Joe', last_name='Bloggs')

    def test_everything_is_configured_properly(self):
        """
        Just creates a user and checks that it exists.
        """
        self.assertTrue(User.objects.filter(pk=self.u.id).exists())
        user = User.objects.get(pk=self.u.id)
        self.assertEquals('Joe', user.first_name)
        self.assertEquals('Bloggs', user.last_name)
        self.assertEquals('Joe Bloggs', user.get_full_name())

    def test_creating_with_optional_fields(self):
        email = 'joeblow@example.com'
        u = User.objects.create_user(first_name='Joe', last_name='Bloggs', email=email)
        self.assertTrue(User.objects.filter(email=email).exists())

    def test_username_equals_id(self):
        self.assertEquals(self.u.username, self.u.id)

    def test_get_full_name(self):
        self.assertEquals('Joe Bloggs', self.u.get_full_name())


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


class DiveOfficerPrivilegesTestCase(APITestCase):

    def setUp(self):
        # Create a club and its dive officer
        self.club = Club.objects.create(name='UCCSAC')
        self.do = User.objects.create_user(first_name='Dave', last_name='Officer')
        self.do.club = self.club
        self.do.save()
        self.do.become_dive_officer()
        # Create another club with one member
        self.club2 = Club.objects.create(name='UCDSAC')
        self.other_user = User.objects.create_user(first_name='Other', last_name='User')
        self.other_user.club = self.club2
        self.other_user.save()

    def test_can_retrieve_user_list(self):
        # Log in
        self.client.force_authenticate(self.do)
        # Retrieve a list of all users
        result = self.client.get(reverse('user-list'))
        self.assertEqual(result.status_code, status.HTTP_200_OK) # Should return 200 OK
        self.assertEqual(len(result.data), 1) # Should not return users from other clubs
        # Create a new user (adding them to the club)
        result = self.client.post(reverse('user-list'), MOCK_USER_DATA)
        self.assertEqual(result.status_code, status.HTTP_201_CREATED) # Should return 201 Created
        # Retrieve a list of all users again
        result = self.client.get(reverse('user-list'))
        self.assertEqual(len(result.data), 2) # Should return a list containing the second user

    def test_only_dive_officer_can_create_users(self):
        self.client.force_authenticate(self.other_user)
        result = self.client.post(reverse('user-list'), MOCK_USER_DATA)
        self.assertEqual(result.status_code, status.HTTP_403_FORBIDDEN)

    def test_dive_officer_can_view_club_qualifications(self):
        d1 = Certificate.objects.create(name='Trainee Diver')
        self.client.force_authenticate(self.do)
        bob = User.objects.create_user(first_name='Bob', last_name='Smith', club=self.do.club)
        bob_d1 = Qualification.objects.create(user=bob, certificate=d1)
        result = self.client.get(reverse('club-qualifications', args=[self.do.club.id]))
        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.assertEqual(len(result.data), 1)
        #print(reverse('club-qualifications', args=[self.do.club.id]))


class UserCreationTestCase(APITestCase):

    def setUp(self):
        # Create a club and a Dive Officer
        self.club = Club.objects.create(name='UCCSAC')
        self.do = User.objects.create_user(first_name='Dave', last_name='Officer')
        self.do.club = self.club
        self.do.save()
        self.do.become_dive_officer()

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

    def test_unauthenticated_users_cannot_create_users(self):
        result = self.client.post(reverse('user-list'), MOCK_USER_DATA)
        self.assertEqual(result.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_regular_users_cannot_create_users(self):
        u = User.objects.create_user(first_name='Normal', last_name='User', club=self.club)
        self.client.force_authenticate(u)
        result = self.client.post(reverse('user-list'), MOCK_USER_DATA)
        self.assertEqual(result.status_code, status.HTTP_403_FORBIDDEN)

    def test_creating_a_user_adds_that_user_to_a_club(self):
        self.client.force_authenticate(self.do)
        result = self.client.post(reverse('user-list'), MOCK_USER_DATA)
        self.assertEqual(result.status_code, status.HTTP_201_CREATED)
        u = User.objects.get(first_name='Joe', last_name='Bloggs')
        self.assertEqual(u.club, self.club)

    def test_creating_a_user_allows_explicit_club_field(self):
        su = User.objects.create_superuser(first_name='Super', last_name='User', password='password')
        dauntsac = Club.objects.create(name='Daunt SAC')
        self.client.force_authenticate(su)
        data = MOCK_USER_DATA.copy()
        data['club'] = dauntsac.id
        result = self.client.post(reverse('user-list'), data)
        self.assertEqual(result.status_code, status.HTTP_201_CREATED)
        u = User.objects.get(first_name='Joe')
        self.assertEqual(u.club, dauntsac)

class QualificationTestCase(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(first_name='Joe', last_name='Bloggs')
        self.d1 = Certificate.objects.create(name='Trainee Diver')

    def test_receive_certificate(self):
        self.user.receive_certificate(self.d1)
        self.assertTrue(Qualification.objects.filter(user=self.user, certificate=self.d1).exists())
