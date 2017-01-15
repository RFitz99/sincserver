from django.core.urlresolvers import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from clubs.models import Club, Region
from courses.models import Course, CourseEnrolment
from qualifications.models import Certificate
from users.models import User

class CourseCreateTestCase(APITestCase):

    def setUp(self):
        # Create a staff member
        dublin_north = Region.objects.create(name='Dublin North')
        national = Club.objects.create(name='National', region=dublin_north)
        self.staff = User.objects.create_user('Staff', 'Member', club=national, is_staff=True)
        # Create a certificate
        self.cert = Certificate.objects.create(name='Trainee Diver')
        # Create a region and a club with a DO
        self.region = Region.objects.create(name='South')
        self.club = Club.objects.create(name='UCCSAC', region=self.region)
        self.do = User.objects.create_user('Dive', 'Officer', club=self.club)
        self.do.become_dive_officer()
        # Create a user
        self.member = User.objects.create_user('Club', 'Member', club=self.club)

    def test_admin_can_create_course(self):
        data = {
            'certificate': self.cert.id,
            'region': self.region.id,
        }
        self.client.force_authenticate(self.staff)
        response = self.client.post(reverse('course-list'), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_admin_can_specify_organizer(self):
        data = {
            'certificate': self.cert.id,
            'organizer': self.do.id,
            'region': self.region.id,
        }
        self.client.force_authenticate(self.staff)
        response = self.client.post(reverse('course-list'), data)
        course = Course.objects.get(id=response.data['id'])
        self.assertEqual(course.organizer, self.do,
                         'Admin should be able to set course organizer')

    def test_unauthenticated_user_cannot_create_course(self):
        data = {
            'certificate': self.cert.id,
        }
        response = self.client.post(reverse('course-list'), data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_do_can_create_course(self):
        data = {
            'certificate': self.cert.id,
        }
        self.client.force_authenticate(self.do)
        response = self.client.post(reverse('course-list'), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_do_can_specify_organizer_from_same_club(self):
        data = {
            'certificate': self.cert.id,
            'organizer': self.member.id,
        }
        self.client.force_authenticate(self.do)
        response = self.client.post(reverse('course-list'), data)
        course = Course.objects.get(id=response.data['id'])
        self.assertEqual(course.organizer, self.member,
                         'DO should be able to specify course organizer from same club')

    def test_do_cannot_specify_organizer_from_other_club(self):
        csac = Club.objects.create(name='CSAC')
        other_member = User.objects.create_user('Other', 'Member', club=csac)
        data = {
            'certificate': self.cert.id,
            'organizer': other_member.id,
        }
        self.client.force_authenticate(self.do)
        response = self.client.post(reverse('course-list'), data)
        course = Course.objects.get(id=response.data['id'])
        self.assertEqual(course.organizer, self.do,
                         'DO should not be able to specify course organizer from another club')

    def test_region_defaults_to_creators_region(self):
        data = {
            'certificate': self.cert.id,
        }
        self.client.force_authenticate(self.do)
        response = self.client.post(reverse('course-list'), data)
        course = Course.objects.get(id=response.data['id'])
        self.assertEqual(course.region, self.do.club.region,
                         'Course region should default to creator\'s region')

    def test_authenticated_user_cannot_create_course(self):
        data = {
            'certificate': self.cert.id,
        }
        self.client.force_authenticate(self.member)
        response = self.client.post(reverse('course-list'), data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN,
                        'Regular user should not be able to create course')
