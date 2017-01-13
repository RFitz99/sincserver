from django.core.urlresolvers import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from clubs.models import Club, Region
from users.models import User

class ClubDetailTestCase(APITestCase):

    def setUp(self):
        # Create a club that we'll try to update
        self.club = Club.objects.create(name='UCC')

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

    def test_do_can_view_detail_of_own_club(self):
        do = User.objects.create_user(first_name='Dave', last_name='Officer', club=self.club)
        do.become_dive_officer()
        self.client.force_authenticate(do)
        response = self.client.get(reverse('club-detail', args=[self.club.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
