from django.core.urlresolvers import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from clubs.models import Club, Region
from courses.models import Course, CourseEnrolment, CourseInstruction
from qualifications.models import Certificate
from users.models import User

class CourseInstructionListTestCase(APITestCase):
    def setUp(self):
        cert = Certificate.objects.create(name='Trainee Diver')
        national = Club.objects.create(name='National', region=Region.objects.create(name='National'))
        self.admin = User.objects.create_user('Staff', 'Member', is_staff=True, club=national)
        self.club = Club.objects.create(name='UCC', region=Region.objects.create(name='South'))
        self.do = User.objects.create_user('Dive', 'Officer', club=self.club)
        self.do.become_dive_officer()
        self.i1 = User.objects.create_user('One', 'Instructor', club=self.club)
        self.i2 = User.objects.create_user('Another', 'Instructor')
        self.course = Course.objects.create(
            certificate=cert,
            creator=self.admin,
            organizer=self.admin,
            region=national.region
        )
        CourseInstruction.objects.create(
            course=self.course,
            user=self.i1,
        )
        CourseInstruction.objects.create(
            course=self.course,
            user=self.i2
        )

    def test_admin_can_view_course_instructions_by_course(self):
        self.client.force_authenticate(self.admin)
        response = self.client.get(reverse('course-instruction-list', args=[self.course.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_admin_can_view_course_instructions_by_user(self):
        self.client.force_authenticate(self.admin)
        response = self.client.get(reverse('user-course-instruction-list', args=[self.i1.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_dive_officer_can_view_course_instructions_by_course_within_club(self):
        self.client.force_authenticate(self.do)
        response = self.client.get(reverse('course-instruction-list', args=[self.course.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_dive_officer_can_view_course_instructions_by_user_within_club(self):
        self.client.force_authenticate(self.do)
        response = self.client.get(reverse('user-course-instruction-list', args=[self.i1.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_unauthenticated_user_cannot_view_course_instructions_by_course(self):
        response = self.client.get(reverse('course-instruction-list', args=[self.course.id]))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_user_cannot_view_course_instructions_by_user(self):
        response = self.client.get(reverse('user-course-instruction-list', args=[self.i1.id]))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_can_view_own_course_instructions_by_course(self):
        self.client.force_authenticate(self.i1)
        response = self.client.get(reverse('course-instruction-list', args=[self.course.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_user_can_view_own_course_instructions_by_user(self):
        self.client.force_authenticate(self.i1)
        response = self.client.get(reverse('user-course-instruction-list', args=[self.i1.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
