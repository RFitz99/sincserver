from django.core.urlresolvers import reverse

from rest_framework import status
from rest_framework.test import APITestCase

<<<<<<< HEAD
from users.models import User
=======
from clubs.models import Club
from qualifications.models import Certificate, Qualification
from users.models import User
from users.tests.shared import MOCK_USER_DATA
>>>>>>> master

class CurrentMembershipStatusTestCase(APITestCase):

    def setUp(self):
      self.staff = User.objects.create_user('Staff', 'Member', is_staff=True)
      club = Club.objects.create(name='UCC')
      self.do = User.objects.create_user('Dive', 'Officer', club=club)
      self.do.become_dive_officer()
      self.member = User.objects.create_user('Club', 'Member', club=club)
      self.other_user = User.objects.create_user('Other', 'User')

    def test_admin_can_view_current_membership_status(self):
      self.client.force_authenticate(self.staff)
      response = self.client.get(reverse('user-current-membership-status', args=[self.member.id]))
      self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_do_can_view_club_member_status(self):
      self.client.force_authenticate(self.do)
      response = self.client.get(reverse('user-current-membership-status', args=[self.member.id]))
      self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_do_cannot_view_non_member_status(self):
      self.client.force_authenticate(self.do)
      response = self.client.get(reverse('user-current-membership-status', args=[self.other_user.id]))
      self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_can_view_own_status(self):
      self.client.force_authenticate(self.member)
      response = self.client.get(reverse('user-current-membership-status', args=[self.member.id]))
      self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_cannot_view_other_user_status(self):
      self.client.force_authenticate(self.member)
      response = self.client.get(reverse('user-current-membership-status', args=[self.other_user.id]))
      self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
