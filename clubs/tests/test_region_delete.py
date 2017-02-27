from datetime import timedelta

from django.core.urlresolvers import reverse
from django.utils import timezone

from rest_framework import status
from rest_framework.test import APITestCase

from clubs.models import Club, Region
from clubs.views import ClubViewSet
from users.models import User

class RegionDeleteTestCase(APITestCase):
    def setUp(self):
        self.region = Region.objects.create(name='South')
        self.foundation_date = timezone.now().date()
        self.club = Club.objects.create(
            name='UCC',
            foundation_date=self.foundation_date,
            region=self.region
        )
        self.staff = User.objects.create_user('Staff', 'Member', is_staff=True)
        self.do = User.objects.create_user('Dive', 'Officer', club=self.club)
        self.do.become_dive_officer()
        self.user = User.objects.create_user('Club', 'Member', club=self.club)

    def test_deleting_region_creates_national_region(self):
        self.region.delete()
        self.assertTrue(Region.objects.filter(name='National').exists())

    def test_deleting_region_assigns_club_to_national(self):
        self.region.delete()
        national = Region.objects.get(name='National')
        club = Club.objects.get(name='UCC')
        self.assertEqual(club.region, national)
