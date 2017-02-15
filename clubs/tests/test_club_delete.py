from django.core.urlresolvers import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from clubs.models import Club, Region
from users.models import User

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

    def test_deleting_club_creates_national_club(self):
        self.ucc.delete()
        self.assertTrue(Club.objects.filter(name='National').exists())

    def test_deleting_club_assigns_members_to_national_club(self):
        self.ucc.delete()
        member = User.objects.get(pk=self.member.pk)
        self.assertEqual(member.club, Club.objects.get(name='National'))
