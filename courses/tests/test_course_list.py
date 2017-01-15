from django.core.urlresolvers import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from clubs.models import Club, Region
from courses.models import Course, CourseEnrolment
from qualifications.models import Certificate
from users.models import User

class CourseListTestCase(APITestCase):

    def setUp(self):
        # Create a region
        self.region = Region.objects.create(name='South')
        # Create a certificate
        cert = Certificate.objects.create(name='Trainee Diver')
        # Create a course and its creator and organizer
        self.creator = User.objects.create_user('Course', 'Creator')
        self.organizer = User.objects.create_user('Course', 'Organizer')
        self.course = Course.objects.create(
            creator=self.creator,
            organizer=self.organizer,
            region=self.region,
            certificate=cert,
        )
        # Create a user
        self.user = User.objects.create_user('Normal', 'User')

    def test_unauthenticated_user_cannot_list_courses(self):
        response = self.client.get(reverse('course-list'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED,
                        'Unauthenticated user shouldn\'t be able to list courses')

    def test_authenticated_user_can_list_courses(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse('course-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                        'Authenticated user should be able to list courses')


class RegionCourseListTestCase(APITestCase):
    def setUp(self):
        self.cert = Certificate.objects.create(name='Trainee Diver')
        # Create a region
        self.region = Region.objects.create(name='South')
        # Create a course
        self.creator = User.objects.create_user('Course', 'Creator')
        self.organizer = User.objects.create_user('Course', 'Organizer')
        self.course = Course.objects.create(
            creator=self.creator,
            organizer=self.organizer,
            region=self.region,
            certificate=self.cert,
        )
        # Create a user
        self.user = User.objects.create_user('Normal', 'User')

    def test_unauthenticated_user_cannot_list_courses_by_region(self):
        response = self.client.get(reverse('region-course-list', args=[self.region.id]))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED,
                        'Unauthenticated user shouldn\'t be able to list courses by region')

    def test_authenticated_user_can_list_courses_by_region(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse('region-course-list', args=[self.region.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                        'Authenticated user should be able to list courses by region')

    def test_list_courses_by_region_returns_all_courses_in_region(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse('region-course-list', args=[self.region.id]))
        self.assertEqual(len(response.data), 1,
                        'Regional course lists should display all courses from region')

    def test_list_courses_by_region_returns_only_courses_in_region(self):
        # Create a course from another region
        north = Region.objects.create(name='North')
        course = Course.objects.create(
            creator=self.creator,
            organizer=self.organizer,
            region=north,
            certificate=self.cert,
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse('region-course-list', args=[self.region.id]))
        self.assertEqual(len(response.data), 1,
                        'Regional course list shouldn\'t list courses from other regions')
