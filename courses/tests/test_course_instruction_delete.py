from django.core.urlresolvers import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from clubs.models import Club, Region
from courses.models import Course, CourseEnrolment, CourseInstruction
from qualifications.models import Certificate
from users.models import User

class CourseInstructionDeleteTestCase(APITestCase):
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
        self.ci1 = CourseInstruction.objects.create(
            course=self.course,
            user=self.i1,
        )
        self.ci2 = CourseInstruction.objects.create(
            course=self.course,
            user=self.i2
        )

    def test_admin_can_delete_course_instruction_by_course(self):
      self.client.force_authenticate(self.admin)
      response = self.client.delete(reverse('course-instruction-detail', args=[self.course.id, self.ci1.id]))
      self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_admin_can_delete_course_instruction_by_user(self):
      self.client.force_authenticate(self.admin)
      response = self.client.delete(reverse('user-course-instruction-detail', args=[self.i1.id, self.ci1.id]))
      self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_dive_officer_can_delete_course_instruction_by_course(self):
      self.client.force_authenticate(self.admin)
      response = self.client.delete(reverse('course-instruction-detail', args=[self.course.id, self.ci1.id]))
      self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_dive_officer_can_delete_course_instruction_by_user(self):
      self.client.force_authenticate(self.admin)
      response = self.client.delete(reverse('user-course-instruction-detail', args=[self.i1.id, self.ci1.id]))
      self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_user_can_delete_own_course_instruction_by_course(self):
      self.client.force_authenticate(self.i1)
      response = self.client.delete(reverse('course-instruction-detail', args=[self.course.id, self.ci1.id]))
      self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_user_can_delete_course_instruction_by_user(self):
      self.client.force_authenticate(self.i1)
      response = self.client.delete(reverse('user-course-instruction-detail', args=[self.i1.id, self.ci1.id]))
      self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
