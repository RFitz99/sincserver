from datetime import timedelta

from django.core.urlresolvers import reverse
from django.utils import timezone

from rest_framework import status
from rest_framework.test import APITestCase

from clubs.models import Club, Region
from clubs.views import ClubViewSet
from users.models import User

class ClubUpdateTestCase(APITestCase):
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

class ClubUpdateStaffTestCase(APITestCase):
    def setUp(self):
        self.region = Region.objects.create(name='South')
        self.foundation_date = timezone.now()
        self.club = Club.objects.create(
            name='UCC',
            foundation_date=self.foundation_date,
            region=self.region
        )
        self.club_id = Club.objects.get(name='UCC').id
        # New data
        self.new_name = 'CSAC'
        self.new_region = Region.objects.create(name='North')
        self.new_date = (timezone.now() - timedelta(days=365)).date()
        data = {
            'foundation_date': self.new_date.strftime('%Y-%m-%d'),
            'name': self.new_name,
            'region': self.new_region.id,
        }
        self.staff = User.objects.create_user('Staff', 'Member', is_staff=True)
        # Authenticate as staff
        self.client.force_authenticate(self.staff)
        self.response = self.client.put(reverse('club-detail', args=[self.club_id]), data)

    def test_staff_can_update_all_fields(self):
        self.assertEqual(self.response.status_code, status.HTTP_200_OK)

    def test_staff_update_changes_club_name(self):
        club = Club.objects.get(id=self.club_id)
        self.assertEqual(club.name, self.new_name)

    def test_staff_update_changes_club_foundation_date(self):
        club = Club.objects.get(id=self.club_id)
        self.assertEqual(club.foundation_date, self.new_date)

    def test_staff_update_changes_club_region(self):
        club = Club.objects.get(id=self.club_id)
        self.assertEqual(club.region, self.new_region,
                        'Admin should be able to change club region')


class ClubUpdateDiveOfficerTestCase(APITestCase):
    def setUp(self):
        self.region = Region.objects.create(name='South')
        self.name = 'UCC'
        self.foundation_date = timezone.now().date()
        self.club = Club.objects.create(
            name=self.name,
            foundation_date=self.foundation_date,
            region=self.region
        )
        self.club_id = Club.objects.get(name='UCC').id

        self.do = User.objects.create_user('Dive', 'Officer', club=self.club)
        self.do.become_dive_officer()

        self.new_name = 'CSAC'
        self.new_region = Region.objects.create(name='North')
        self.new_date = (timezone.now() - timedelta(days=365)).date()
        data = {
            'foundation_date': self.new_date.strftime('%Y-%m-%d'),
            'name': self.new_name,
            'region': self.new_region.id,
        }
        self.client.force_authenticate(self.do)
        self.response = self.client.put(reverse('club-detail', args=[self.club_id]), data)

    def test_dive_officer_can_update(self):
        self.assertEqual(self.response.status_code, status.HTTP_200_OK,
                        'DO should be able to update club details')

    def test_dive_officer_cannot_change_name(self):
        club = Club.objects.get(id=self.club_id)
        self.assertEqual(club.name, self.name,
                        'DO shouldn\'t be able to change club name')

    def test_dive_officer_cannot_change_region(self):
        club = Club.objects.get(id=self.club_id)
        self.assertEqual(club.region, self.region,
                        'Dive Officer shouldn\'t be able to change club region')

    def test_dive_officer_can_change_foundation_date(self):
        club = Club.objects.get(id=self.club_id)
        self.assertEqual(club.foundation_date, self.new_date,
                        'Dive Officer should be able to change club foundation date')


class ClubUpdateMemberTestCase(APITestCase):
    def setUp(self):
        self.region = Region.objects.create(name='South')
        self.name = 'UCC'
        self.foundation_date = timezone.now().date()
        self.club = Club.objects.create(
            name=self.name,
            foundation_date=self.foundation_date,
            region=self.region
        )
        self.club_id = Club.objects.get(name='UCC').id


        self.new_name = 'CSAC'
        self.new_region = Region.objects.create(name='North')
        self.new_date = (timezone.now() - timedelta(days=365)).date()
        data = {
            'foundation_date': self.new_date.strftime('%Y-%m-%d'),
            'name': self.new_name,
            'region': self.new_region.id,
        }

        self.member = User.objects.create_user('Staff', 'Member', club=self.club)
        self.client.force_authenticate(self.member)
        self.response = self.client.put(reverse('club-detail', args=[self.club_id]), data)

    def test_member_cannot_update(self):
        self.assertEqual(self.response.status_code, status.HTTP_403_FORBIDDEN)

    def test_member_cannot_change_name(self):
        club = Club.objects.get(id=self.club_id)
        self.assertEqual(club.name, self.name)

    def test_member_cannot_change_region(self):
        club = Club.objects.get(id=self.club_id)
        self.assertEqual(club.region, self.region)

    def test_member_cannot_change_foundation_date(self):
        club = Club.objects.get(id=self.club_id)
        self.assertEqual(club.foundation_date, self.foundation_date)
