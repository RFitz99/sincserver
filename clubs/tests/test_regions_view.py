from django.core.urlresolvers import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from clubs.models import Club, Region
from users.models import User

class RegionDeleteTestCase(APITestCase):

    def setUp(self):
        self.south = Region.objects.create(name='south')
        self.ucc = Club.objects.create(name='UCC', region=self.south)
        self.member = User.objects.create_user('Club', 'Member', club=self.ucc)

    def test_admin_can_delete_region(self):
        self.client.force_authenticate(User.objects.create_superuser('Super', 'User', 'pass'))
        response = self.client.delete(reverse('region-detail', args=[self.south.id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Region.objects.filter(name='south').exists())

    def test_deleting_region_does_not_delete_clubs(self):
        self.client.force_authenticate(User.objects.create_superuser('Super', 'User', 'pass'))
        response = self.client.delete(reverse('region-detail', args=[self.south.id]))
        self.assertTrue(Club.objects.filter(name='UCC').exists())
