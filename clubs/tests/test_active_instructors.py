from django.core.urlresolvers import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from clubs.models import Club, Region
from qualifications.models import Certificate, Qualification
from users.models import User

class ActiveInstructorsTestCase(APITestCase):

    def setUp(self):
        # Create a region
        self.south = Region.objects.create(name='South')
        # Create an instructor cert
        self.mon1 = Certificate.objects.create(name='Mon 1', is_instructor_certificate=True)
        # Create some clubs
        self.ucc = Club.objects.create(name='UCC', region=self.south)
        self.csac = Club.objects.create(name='Cork', region=self.south)
        # Create some instructors in the south region
        self.u1 = User.objects.create_user(first_name='Joe', last_name='Bloggs', club=self.ucc)
        self.u1.receive_certificate(self.mon1)
        self.u2 = User.objects.create_user(first_name='Nosmo', last_name='King', club=self.csac)
        self.u2.receive_certificate(self.mon1)
        # Create an instructor in a different region
        self.north = Region.objects.create(name='North')
        self.belfast = Club.objects.create(name='Belfast')
        self.u3 = User.objects.create_user(first_name='SomeOther', last_name='RegionalInstructor')
        self.u3.receive_certificate(self.mon1)
        # Create a user who isn't authorized to see the list
        self.pleb = User.objects.create_user(first_name='Unauthorized', last_name='User', club=self.ucc)
        # Create a UCC Dive Officer who can see all regional instructors
        self.do = User.objects.create_user(first_name='Dave', last_name='Officer', club=self.ucc)
        self.do.become_dive_officer()
        # Create a Training Officer who can see all regional instructors
        self.to = User.objects.create_user(first_name='Theo', last_name='Didaktikos', club=self.ucc)
        self.to.become_dive_officer()

    def test_unauthenticated_access_fails(self):
        result = self.client.get(reverse('region-active-instructors', args=[self.south.id]))
        self.assertEqual(result.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_non_committee_access_fails(self):
        self.client.force_authenticate(self.pleb)
        result = self.client.get(reverse('region-active-instructors', args=[self.south.id]))
        self.assertEqual(result.status_code, status.HTTP_403_FORBIDDEN)

    def test_dive_officer_can_view_own_region(self):
        expected_result_length = User.objects.filter(
            club__region=self.south,
            qualifications__certificate__is_instructor_certificate=True
        ).count()
        self.client.force_authenticate(self.do)
        result = self.client.get(reverse('region-active-instructors', args=[self.south.id]))
        self.assertEqual(result.status_code, status.HTTP_200_OK)
        data = result.data
        self.assertEqual(len(data), expected_result_length)

    def test_dive_officer_cannot_view_other_region(self):
        self.client.force_authenticate(self.do)
        result = self.client.get(reverse('region-active-instructors', args=[self.north.id]))
        self.assertEqual(result.status_code, status.HTTP_403_FORBIDDEN)

    def test_training_officer_can_view(self):
        expected_result_length = User.objects.filter(
            club__region=self.south,
            qualifications__certificate__is_instructor_certificate=True
        ).count()
        self.client.force_authenticate(self.to)
        result = self.client.get(reverse('region-active-instructors', args=[self.south.id]))
        self.assertEqual(result.status_code, status.HTTP_200_OK)
        data = result.data
        self.assertEqual(len(data), expected_result_length)

    def test_admin_can_view(self):
        expected_result_length = User.objects.filter(
            club__region=self.south,
            qualifications__certificate__is_instructor_certificate=True
        ).count()
        su = User.objects.create_superuser(first_name='Super', last_name='User', password='password')
        self.client.force_authenticate(su)
        result = self.client.get(reverse('region-active-instructors', args=[self.south.id]))
        self.assertEqual(result.status_code, status.HTTP_200_OK)
        data = result.data
        self.assertEqual(len(data), expected_result_length)

    def test_rdo_can_view(self):
        expected_result_length = User.objects.filter(
            club__region=self.south,
            qualifications__certificate__is_instructor_certificate=True
        ).count()
        rdo = User.objects.create_user(first_name='Regional', last_name='Dive-Officer')
        self.south.dive_officer = rdo
        self.south.save()
        self.client.force_authenticate(rdo)
        self.assertTrue(rdo.is_regional_dive_officer())
        result = self.client.get(reverse('region-active-instructors', args=[self.south.id]))
        self.assertEqual(result.status_code, status.HTTP_200_OK)
        data = result.data
        self.assertEqual(len(data), expected_result_length)
