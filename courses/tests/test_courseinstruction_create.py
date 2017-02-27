from django.core.urlresolvers import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from clubs.models import Club, Region
from courses.models import Course, CourseEnrolment, CourseInstruction
from qualifications.models import Certificate
from users.models import User

class CourseInstructionCreateTestCase(APITestCase):
    def setUp(self):
        cert = Certificate.objects.create(name='Trainee Diver')
        national = Club.objects.create(name='National', region=Region.objects.create(name='National'))
        self.admin = User.objects.create_user('Staff', 'Member', is_staff=True, club=national)
        self.club = Club.objects.create(name='UCC', region=Region.objects.create(name='South'))
        self.do = User.objects.create_user('Dive', 'Officer', club=self.club)
        self.do.become_dive_officer()
        self.i1 = User.objects.create_user('One', 'Instructor', club=self.club)
        self.i2 = User.objects.create_user('Another', 'Instructor')
        self.organizer = User.objects.create_user('Course', 'Organizer', club=self.club)
        self.course = Course.objects.create(
            certificate=cert,
            creator=self.admin,
            organizer=self.organizer,
            region=national.region
        )

    def test_admin_can_add_instructor(self):
      self.client.force_authenticate(self.admin)
      data = {
        'course': self.course.id,
        'user': self.i1.id
      }
      response = self.client.post(reverse('course-instruction-list', args=[self.course.id]), data)
      self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_organizer_can_add_instructor_from_club(self):
      self.client.force_authenticate(self.organizer)
      data = {
        'course': self.course.id,
        'user': self.i1.id
      }
      response = self.client.post(reverse('course-instruction-list', args=[self.course.id]), data)
      self.assertEqual(response.status_code, status.HTTP_201_CREATED)
