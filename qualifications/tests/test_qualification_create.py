from django.core.urlresolvers import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from clubs.models import Club
from qualifications.models import Certificate, Qualification
from users.models import User

class QualificationCreateTestCase(APITestCase):
    def setUp(self):
        self.cert = Certificate.objects.create(name='Trainee Diver')
        self.club = Club.objects.create(name='UCC')
        self.do = User.objects.create_user('Dive', 'Officer', club=self.club)
        self.do.become_dive_officer()
        self.staff = User.objects.create_user('Staff', 'Member', is_staff=True)
        self.member = User.objects.create_user('Club', 'Member', club=self.club)
        self.other_user = User.objects.create_user(
            'Other', 'User',
            club=Club.objects.create(name='CSAC')
        )
        # self.member.receive_certificate(cert)
        # self.other_user.receive_certificate(cert)
        self.data = {
          'user': self.member.id,
          'certificate': self.cert.id,
        }

    def test_unauthenticated_user_cannot_create_qualification(self):
      response = self.client.post(reverse('qualification-list'), self.data, format='json')
      self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_admin_can_create_qualification(self):
      self.client.force_authenticate(self.staff)
      response = self.client.post(reverse('qualification-list'), self.data)
      self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_dive_officer_cannot_create_qualification(self):
      self.client.force_authenticate(self.do)
      response = self.client.post(reverse('qualification-list'), self.data, format='json')
      self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_cannot_create_qualification(self):
      self.client.force_authenticate(self.member)
      response = self.client.post(reverse('qualification-list'), self.data, format='json')
      self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
