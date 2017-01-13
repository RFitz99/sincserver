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
        # The expected length of the results on success will be the number
        # of instructors in the south region.
        self.num_instructors_in_south = User.objects.filter(
            club__region=self.south,
            qualifications__certificate__is_instructor_certificate=True
        ).count()
        # Create an RDO for the south region
        self.rdo = User.objects.create_user(first_name='Regional', last_name='DO')
        self.south.dive_officer = self.rdo
        self.south.save()
        # Create an instructor in a different region
        self.north = Region.objects.create(name='North')
        self.belfast = Club.objects.create(name='Belfast')
        self.u3 = User.objects.create_user(first_name='Northern', last_name='Instructor')
        self.u3.receive_certificate(self.mon1)
        # Create a user who isn't authorized to see the list
        self.pleb = User.objects.create_user(first_name='Normal', last_name='User', club=self.ucc)
        # Create a UCC Dive Officer who can see all regional instructors
        self.do = User.objects.create_user(first_name='Dave', last_name='Officer', club=self.ucc)
        self.do.become_dive_officer()
        # Create a Training Officer who can see all regional instructors
        self.to = User.objects.create_user(first_name='Theo', last_name='Didaktikos', club=self.ucc)
        self.to.become_dive_officer()

    ###########################################################################
    # Administrators can view lists of active instructors for any region.
    ###########################################################################

    def test_admin_can_list_active_instructors(self):
        staff = User.objects.create_user('Staff', 'User', is_staff=True)
        self.client.force_authenticate(staff)
        result = self.client.get(reverse('region-active-instructors', args=[self.south.id]))
        self.assertEqual(result.status_code, status.HTTP_200_OK)
        expected_result_length = self.num_instructors_in_south
        self.assertEqual(len(result.data), expected_result_length)

    ###########################################################################
    # RDOs, DOs, and TOs can view lists of active instructors for their own
    # region, but not for other regions.
    ###########################################################################

    def test_rdo_can_list_active_instructors_in_same_region(self):
        expected_result_length = self.num_instructors_in_south
        self.client.force_authenticate(self.rdo)
        result = self.client.get(reverse('region-active-instructors', args=[self.south.id]))
        self.assertEqual(result.status_code, status.HTTP_200_OK)
        data = result.data
        self.assertEqual(len(data), expected_result_length)

    def test_rdo_cannot_list_active_instructors_in_other_region(self):
        self.client.force_authenticate(self.rdo)
        result = self.client.get(reverse('region-active-instructors', args=[self.north.id]))
        self.assertEqual(result.status_code, status.HTTP_403_FORBIDDEN)

    def test_dive_officer_can_list_active_instructors_in_same_region(self):
        self.client.force_authenticate(self.do)
        result = self.client.get(reverse('region-active-instructors', args=[self.south.id]))
        self.assertEqual(result.status_code, status.HTTP_200_OK)
        expected_result_length = self.num_instructors_in_south
        self.assertEqual(len(result.data), expected_result_length)

    def test_dive_officer_cannot_list_active_instructors_in_other_region(self):
        self.client.force_authenticate(self.do)
        result = self.client.get(reverse('region-active-instructors', args=[self.north.id]))
        self.assertEqual(result.status_code, status.HTTP_403_FORBIDDEN)

    def test_training_officer_can_list_active_instructors_in_other_region(self):
        self.client.force_authenticate(self.to)
        result = self.client.get(reverse('region-active-instructors', args=[self.south.id]))
        self.assertEqual(result.status_code, status.HTTP_200_OK)
        expected_result_length = self.num_instructors_in_south
        self.assertEqual(len(result.data), expected_result_length)

    def test_training_officer_cannot_list_active_instructors_in_other_region(self):
        expected_result_length = self.num_instructors_in_south
        self.client.force_authenticate(self.to)
        result = self.client.get(reverse('region-active-instructors', args=[self.north.id]))
        self.assertEqual(result.status_code, status.HTTP_403_FORBIDDEN)

    ###########################################################################
    # Unauthenticated and regular users cannot list active instructors.
    ###########################################################################

    def test_unauthenticated_user_cannot_list_active_instructors(self):
        result = self.client.get(reverse('region-active-instructors', args=[self.south.id]))
        self.assertEqual(result.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_cannot_list_active_instructors(self):
        self.client.force_authenticate(self.pleb)
        result = self.client.get(reverse('region-active-instructors', args=[self.south.id]))
        self.assertEqual(result.status_code, status.HTTP_403_FORBIDDEN)
