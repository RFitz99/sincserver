from django.core.urlresolvers import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from clubs.models import Club, Region
from users.models import User

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
