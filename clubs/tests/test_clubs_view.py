from django.core.urlresolvers import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from clubs.models import Club, Region
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
        response = self.client.get(reverse('club-detail', args=[self.club.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_member_cannot_view_clubs_list(self):
        member = User.objects.create_user(first_name='Normal', last_name='User', club=self.club)
        self.client.force_authenticate(member)
        response = self.client.get(reverse('club-list'))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_member_cannot_view_own_clubs_detail(self):
        member = User.objects.create_user(first_name='Normal', last_name='User', club=self.club)
        self.client.force_authenticate(member)
        response = self.client.get(reverse('club-detail', args=[self.club.id]))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_member_cannot_view_other_clubs_detail(self):
        csac = Club.objects.create(name='Cork')
        member = User.objects.create_user(first_name='Normal', last_name='User', club=self.club)
        self.client.force_authenticate(member)
        response = self.client.get(reverse('club-detail', args=[csac.id]))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

class ClubCreateTestCase(APITestCase):

    def setUp(self):
        self.staff = User.objects.create_user(first_name='Staff', last_name='Member', is_staff=True)

    def test_staff_can_create_club(self):
        region = Region.objects.create(name='South')
        self.client.force_authenticate(self.staff)
        data = {
            'name': 'Daunt',
            'region': region.id,
        }
        response = self.client.post(reverse('club-list'), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_unauthenticated_user_cannot_create_club(self):
        data = {
            'name': 'Daunt',
        }
        response = self.client.post(reverse('club-list'), data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_do_cannot_create_club(self):
        ucc = Club.objects.create(name='UCC')
        do = User.objects.create_user('Dave', 'Officer', club=ucc)
        do.become_dive_officer()
        do.save()
        self.client.force_authenticate(do)
        data = {
            'name': 'Daunt',
        }
        response = self.client.post(reverse('club-list'), data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_rdo_cannot_create_club(self):
        region = Region.objects.create(name='South')
        ucc = Club.objects.create(name='UCC', region=region)
        rdo = User.objects.create_user('Dave', 'Officer', club=ucc)
        rdo.save()
        self.client.force_authenticate(rdo)
        data = {
            'name': 'Daunt',
        }
        response = self.client.post(reverse('club-list'), data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class ClubDeleteTestCase(APITestCase):

    def setUp(self):
        self.ucc = Club.objects.create(name='UCC')
        self.member = User.objects.create_user('Club', 'Member', club=self.ucc)

    def test_admin_can_delete_club(self):
        self.client.force_authenticate(User.objects.create_superuser('Super', 'User', 'password'))
        response = self.client.delete(reverse('club-detail', args=[self.ucc.id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Club.objects.filter(name='UCC').exists())

    def test_do_cannot_delete_their_own_club(self):
        do = User.objects.create_user('Dave', 'Officer', club=self.ucc)
        do.become_dive_officer()
        do.save()
        self.client.force_authenticate(do)
        response = self.client.delete(reverse('club-detail', args=[self.ucc.id]))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Club.objects.filter(name='UCC').exists())

    def test_deleting_club_preserves_its_members(self):
        member = User.objects.get(first_name='Club')
        self.client.force_authenticate(User.objects.create_superuser('Super', 'User', 'password'))
        response = self.client.delete(reverse('club-detail', args=[self.ucc.id]))
        self.assertFalse(Club.objects.filter(name='UCC').exists())
        self.assertTrue(User.objects.filter(first_name='Club').exists())
