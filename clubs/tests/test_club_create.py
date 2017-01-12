from django.core.urlresolvers import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from clubs.models import Club, Region
from users.models import User

class ClubCreateTestCase(APITestCase):

    def setUp(self):
        self.staff = User.objects.create_user(first_name='Staff', last_name='Member', is_staff=True)
        # Create a club and a DO
        region = Region.objects.create(name='South')
        ucc = Club.objects.create(name='UCC', region=region)
        self.do = User.objects.create_user('Dave', 'Officer', club=ucc)
        self.do.become_dive_officer()
        self.do.save()
        # Create an RDO
        self.rdo = User.objects.create_user('Dave', 'Officer', club=ucc)
        self.rdo.save()
        # Create a normal user
        self.user = User.objects.create_user('Normal', 'User')
        # Create some new club data
        self.data = {
            'name': 'Daunt',
            'region': region.id,
        }

    ###########################################################################
    # Administrators can create clubs.
    ###########################################################################

    def test_admin_can_create_club(self):
        self.client.force_authenticate(self.staff)
        response = self.client.post(reverse('club-list'), self.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    ###########################################################################
    # Nobody else can create clubs:
    ###########################################################################

    def test_unauthenticated_user_cannot_create_club(self):
        response = self.client.post(reverse('club-list'), self.data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_cannot_create_club(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(reverse('club-list'), self.data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_do_cannot_create_club(self):
        self.client.force_authenticate(self.do)
        response = self.client.post(reverse('club-list'), self.data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_rdo_cannot_create_club(self):
        self.client.force_authenticate(self.rdo)
        response = self.client.post(reverse('club-list'), self.data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
