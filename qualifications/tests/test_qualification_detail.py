from django.core.urlresolvers import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from clubs.models import Club
from qualifications.models import Certificate, Qualification
from users.models import User

class QualificationDetailTestCase(APITestCase):
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

    def test_unauthenticated_user_cannot_view_qualification_detail(self):
        cert = Qualification.objects.get(user=self.member)
        response = self.client.get(reverse('qualification-detail', args=[cert.id]))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_admin_can_view_qualification_detail(self):
        cert = Qualification.objects.get(user=self.member)
        self.client.force_authenticate(self.staff)
        response = self.client.get(reverse('qualification-detail', args=[cert.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_dive_officer_can_view_qualification_detail_in_same_club(self):
        qual = Qualification.objects.get(user=self.member)
        self.client.force_authenticate(self.do)
        response = self.client.get(reverse('qualification-detail', args=[qual.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_dive_officer_cannot_view_qualification_detail_in_other_club(self):
        qual = Qualification.objects.get(user=self.other_user)
        self.client.force_authenticate(self.do)
        response = self.client.get(reverse('qualification-detail', args=[qual.id]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_can_view_own_qualification_detail(self):
        qual = Qualification.objects.get(user=self.member)
        self.client.force_authenticate(self.member)
        response = self.client.get(reverse('qualification-detail', args=[qual.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_cannot_view_other_users_qualification_detail(self):
        qual = Qualification.objects.get(user=self.other_user)
        self.client.force_authenticate(self.member)
        response = self.client.get(reverse('qualification-detail', args=[qual.id]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
