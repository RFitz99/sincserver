from django.core.urlresolvers import reverse
from faker import Faker
from rest_framework import status
from rest_framework.test import APITestCase

from clubs.models import Club
from qualifications.models import Certificate, Qualification
from users.models import User

fake = Faker()

class QualificationPatchTestCase(APITestCase):
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

    def test_admin_can_update_qualification_date(self):
        qual = Qualification.objects.get(user=self.member)
        date = fake.date_time_this_century().date().strftime('%Y-%m-%d')
        data = {'date_granted': date}
        self.client.force_authenticate(self.staff)
        response = self.client.patch(reverse('qualification-detail', args=[qual.id]), data)
        # Check HTTP status
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check response data
        self.assertEqual(response.data['date_granted'], date)
        # Check database
        self.assertEqual(
            Qualification.objects.get(user=self.member).date_granted.strftime('%Y-%m-%d'),
            date
        )

    def test_admin_can_update_qualification_certificate(self):
        qual = Qualification.objects.get(user=self.member)
        cert = Certificate.objects.create(name='Club Diver')
        data = {'certificate': cert.id}
        self.client.force_authenticate(self.staff)
        response = self.client.patch(reverse('qualification-detail', args=[qual.id]), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check response data
        self.assertEqual(response.data['certificate'], cert.id)
        # Check database
        self.assertEqual(
            Qualification.objects.get(user=self.member).certificate,
            cert
        )

    def test_admin_can_update_qualification_user(self):
        qual = Qualification.objects.get(user=self.member)
        data = {'user': self.other_user.id}
        self.client.force_authenticate(self.staff)
        response = self.client.patch(reverse('qualification-detail', args=[qual.id]), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check response data
        self.assertEqual(response.data['user'], self.other_user.id)
        # Check database
        self.assertFalse(
            Qualification.objects.filter(user=self.member).exists()
        )

    def test_unauthenticated_user_cannot_update_qualification_date(self):
        qual = Qualification.objects.get(user=self.member)
        original_date = qual.date_granted
        date = fake.date_time_this_century().date().strftime('%Y-%m-%d')
        data = {'date_granted': date}
        response = self.client.patch(reverse('qualification-detail', args=[qual.id]), data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        # Check database
        self.assertEqual(
            Qualification.objects.get(user=self.member).date_granted,
            original_date
        )

    def test_user_cannot_update_qualification_date(self):
        qual = Qualification.objects.get(user=self.member)
        original_date = qual.date_granted
        date = fake.date_time_this_century().date().strftime('%Y-%m-%d')
        data = {'date_granted': date}
        self.client.force_authenticate(self.member)
        response = self.client.patch(reverse('qualification-detail', args=[qual.id]), data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        # Check database
        self.assertEqual(
            Qualification.objects.get(user=self.member).date_granted,
            original_date
        )

    def test_dive_officer_cannot_update_qualification_date(self):
        qual = Qualification.objects.get(user=self.member)
        original_date = qual.date_granted
        date = fake.date_time_this_century().date().strftime('%Y-%m-%d')
        data = {'date_granted': date}
        self.client.force_authenticate(self.do)
        response = self.client.patch(reverse('qualification-detail', args=[qual.id]), data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        # Check database
        self.assertEqual(
            Qualification.objects.get(user=self.member).date_granted,
            original_date
        )
