from django.core.urlresolvers import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from clubs.models import Club, CommitteePosition, Region
from qualifications.models import Certificate, Qualification
from users.models import User
from users.tests.shared import MOCK_USER_DATA

###############################################################################
# These tests check our assumptions about how users are deleted.
###############################################################################

class UserDeletionTestCase(APITestCase):

  def setUp(self):
    self.admin = User.objects.create_user('Staff', 'Member', is_staff=True)
    self.region = Region.objects.create(name='South')
    self.club = Club.objects.create(name='UCCSAC', region=self.region)
    self.do = User.objects.create_user('Dave', 'Officer', club=self.club)
    self.do.become_dive_officer()
    self.same_club_member = User.objects.create_user('Same', 'McClubMember', club=self.club)
    self.other_club = Club.objects.create(name='CSAC', region=self.region)
    self.other_club_member = User.objects.create_user('Other', 'McClubMember', club=self.club)

  #############################################################################
  # Administrators can delete users. Nobody else can delete users.
  #############################################################################

  def test_admin_can_delete_users(self):
    self.client.force_authenticate(self.admin)
    response = self.client.delete(reverse('user-detail', args=[self.same_club_member.id]))
    self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

  def test_admin_can_delete_dive_officers(self):
    self.client.force_authenticate(self.admin)
    response = self.client.delete(reverse('user-detail', args=[self.do.id]))
    self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

  def test_dive_officer_cannot_delete_users_in_same_club(self):
    self.client.force_authenticate(self.do)
    response = self.client.delete(reverse('user-detail', args=[self.same_club_member.id]))
    self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

  def test_dive_officer_cannot_delete_themselves(self):
    self.client.force_authenticate(self.do)
    response = self.client.delete(reverse('user-detail', args=[self.do.id]))
    self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

  def test_dive_officer_cannot_delete_users_in_another_club(self):
    self.client.force_authenticate(self.do)
    response = self.client.delete(reverse('user-detail', args=[self.other_club_member.id]))
    self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

  def test_unauthenticated_user_cannot_delete_users(self):
    response = self.client.delete(reverse('user-detail', args=[self.same_club_member.id]))
    self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

  def test_user_cannot_delete_themselves(self):
    self.client.force_authenticate(self.same_club_member)
    response = self.client.delete(reverse('user-detail', args=[self.same_club_member.id]))
    self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

  def test_user_cannot_delete_another_user(self):
    self.client.force_authenticate(self.same_club_member)
    response = self.client.delete(reverse('user-detail', args=[self.other_club_member.id]))
    self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


  #############################################################################
  # Check that qualifications and committee positions are deleted when
  # their User is deleted.
  #############################################################################

  def test_deleting_user_deletes_qualification(self):
    cert = Certificate.objects.create(name='Certificate')
    self.client.force_authenticate(self.admin)
    self.same_club_member.receive_certificate(cert)
    response = self.client.delete(reverse('user-detail', args=[self.same_club_member.id]))
    self.assertFalse(Qualification.objects.filter(user=self.same_club_member).exists())

  def test_deleting_user_deletes_committeeposition(self):
    self.client.force_authenticate(self.admin)
    response = self.client.delete(reverse('user-detail', args=[self.do.id]))
    self.assertFalse(CommitteePosition.objects.filter(user=self.do).exists())
