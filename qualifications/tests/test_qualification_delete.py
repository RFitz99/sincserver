from django.core.urlresolvers import reverse
from faker import Faker
from rest_framework import status
from rest_framework.test import APITestCase

from clubs.models import Club
from qualifications.models import Certificate, Qualification
from users.models import User

class QualificationDeleteTestCase(APITestCase):
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

    def test_admin_can_delete_qualification(self):
        qual = Qualification.objects.get(user=self.member)
        self.client.force_authenticate(self.staff)
        response = self.client.delete(reverse('qualification-detail', args=[qual.id]))
        # Check HTTP status
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        # Check database
        self.assertFalse(
            Qualification.objects.filter(user=self.member).exists()
        )

    def test_unauthenticated_user_cannot_delete_qualification(self):
        qual = Qualification.objects.get(user=self.member)
        response = self.client.delete(reverse('qualification-detail', args=[qual.id]))
        # Check HTTP status
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        # Check database
        self.assertTrue(
            Qualification.objects.filter(user=self.member).exists()
        )

    def test_user_cannot_delete_qualification(self):
        qual = Qualification.objects.get(user=self.member)
        self.client.force_authenticate(self.member)
        response = self.client.delete(reverse('qualification-detail', args=[qual.id]))
        # Check HTTP status
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        # Check database
        self.assertTrue(
            Qualification.objects.filter(user=self.member).exists()
        )

    def test_dive_officer_cannot_delete_qualification(self):
        qual = Qualification.objects.get(user=self.member)
        self.client.force_authenticate(self.do)
        response = self.client.delete(reverse('qualification-detail', args=[qual.id]))
        # Check HTTP status
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        # Check database
        self.assertTrue(
            Qualification.objects.filter(user=self.member).exists()
        )
