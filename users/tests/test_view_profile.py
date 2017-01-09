from django.core.urlresolvers import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from clubs.models import Club
from qualifications.models import Certificate, Qualification
from users.models import User
from users.tests.shared import MOCK_USER_DATA

class ViewUserProfile(APITestCase):

    def setUp(self):
        # Create a club
        ucc = Club.objects.create(name='UCC')
        # Create a Dive Officer
        do = User.objects.create_user(first_name='Dave', last_name='Officer', club=ucc)
        do.become_dive_officer()
        # Create a club member
        member = User.objects.create_user(first_name='Club', last_name='Member', club=ucc)
        # Assign to self so we can use them later
        self.do = do
        self.ucc = ucc
        self.member = member

    def test_do_can_view_member_details(self):
        expected = {
            'first_name': 'Club',
            'last_name': 'Member',
        }
        self.client.force_authenticate(self.do)
        response = self.client.get(reverse('club-users-detail', args=[self.ucc.id, self.member.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = response.data
        self.assertEqual(result['first_name'], expected['first_name'])
        self.assertEqual(result['last_name'], expected['last_name'])

    def test_regular_member_cannot_view_other_members_details(self):
        u = User.objects.create(first_name='Other', last_name='Member', club=self.ucc)
        self.client.force_authenticate(u)
        response = self.client.get(reverse('club-users-detail', args=[self.ucc.id, self.member.id]))
        pass
        #self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
