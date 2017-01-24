from django.core.urlresolvers import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from clubs.models import Club
from qualifications.models import Certificate, Qualification
from users.models import User

class QualificationListTestCase(APITestCase):

    def setUp(self):
        cert = Certificate.objects.create(name='Trainee Diver')
        self.club = Club.objects.create(name='UCC')
        self.do = User.objects.create_user('Dive', 'Officer', club=self.club)
        self.do.become_dive_officer()
        self.staff = User.objects.create_user('Staff', 'Member', is_staff=True)
        self.member = User.objects.create_user('Club', 'Member', club=self.club)
        self.other_user = User.objects.create_user(
            'Other', 'User',
            club=Club.objects.create(name='CSAC')
        )
        self.member.receive_certificate(cert)
        self.other_user.receive_certificate(cert)

    def test_unauthenticated_user_cannot_list_qualifications(self):
        response = self.client.get(reverse('qualification-list'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_can_list_qualifications(self):
        self.client.force_authenticate(self.member)
        response = self.client.get(reverse('qualification-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_sees_their_qualifications(self):
        self.client.force_authenticate(self.member)
        response = self.client.get(reverse('qualification-list'))
        data = response.data
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['user']['id'], self.member.id)

    def test_dive_officer_can_list_qualifications(self):
        self.client.force_authenticate(self.do)
        response = self.client.get(reverse('qualification-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_dive_officer_sees_club_qualifications(self):
        self.client.force_authenticate(self.do)
        response = self.client.get(reverse('qualification-list'))
        data = response.data
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['user']['id'], self.member.id)

    def test_admin_can_list_qualifications(self):
        self.client.force_authenticate(self.staff)
        response = self.client.get(reverse('qualification-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_admin_sees_all_qualifications(self):
        self.client.force_authenticate(self.staff)
        response = self.client.get(reverse('qualification-list'))
        data = response.data
        self.assertEqual(len(data), 2)
