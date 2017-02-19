from django.core.urlresolvers import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from clubs.models import Club, Region
from courses.models import Course, CourseEnrolment
from qualifications.models import Certificate
from users.models import User

class CourseUpdateTestCase(APITestCase):

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
        # Create a course
        self.course = Course.objects.create(
            certificate=self.cert,
            creator=self.do,
            organizer=self.do,
            region=self.region
        )

    def test_admin_can_update_course_region(self):
        region = Region.objects.create(name='North')
        data = {
            'region': region.id,
        }
        self.client.force_authenticate(self.staff)
        response = self.client.patch(reverse('course-detail', args=[self.course.id]), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Course.objects.get(pk=self.course.pk).region, region)

    def test_admin_can_update_course_certificate(self):
        new_cert = Certificate.objects.create(name='Club Diver')
        data = {'certificate': new_cert.id}
        self.client.force_authenticate(self.staff)
        response = self.client.patch(reverse('course-detail', args=[self.course.id]), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Course.objects.get(pk=self.course.pk).certificate, new_cert)
    
    def test_admin_can_update_course_organizer(self):
        data = {'organizer': self.member.id}
        self.client.force_authenticate(self.staff)
        response = self.client.patch(reverse('course-detail', args=[self.course.id]), data)
        # Status code OK?
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Change made?
        self.assertEqual(Course.objects.get(pk=self.course.pk).organizer, self.member)

    def test_admin_can_change_instructors(self):
        i1 = User.objects.create_user('One', 'Instructor')
        i2 = User.objects.create_user('Another', 'Instructor')
        data = {'instructors': [i.id for i in [i1, i2]]}
        self.client.force_authenticate(self.staff)
        response = self.client.patch(reverse('course-detail', args=[self.course.id]), data, format='json')
        # Status code OK?
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Change made?
        instructors = Course.objects.get(pk=self.course.pk).instructors.all()
        self.assertEqual(len(instructors), 2)
        self.assertIn(i1, instructors)
        self.assertIn(i2, instructors)

    def test_do_can_change_organizer_within_club(self):
        data = {'organizer': self.member.id}
        self.client.force_authenticate(self.do)
        response = self.client.patch(reverse('course-detail', args=[self.course.id]), data)
        # Status code OK?
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Change made?
        self.assertEqual(Course.objects.get(pk=self.course.pk).organizer, self.member)

    def test_do_cannot_change_organizer_outside_club(self):
        other_user = User.objects.create_user('Another', 'User')
        data = {'organizer': other_user.id}
        self.client.force_authenticate(self.do)
        response = self.client.patch(reverse('course-detail', args=[self.course.id]), data)
        # Status code OK? (Because setting the organizer uses a fallback, this
        # request won't fail, but it won't change the organizer)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Change not made?
        self.assertEqual(Course.objects.get(pk=self.course.pk).organizer, self.do)

    def test_user_cannot_update_course_region(self):
        old_region = self.course.region
        new_region = Region.objects.create(name='North')
        data = {
            'region': new_region.id,
        }
        self.client.force_authenticate(self.member)
        response = self.client.patch(reverse('course-detail', args=[self.course.id]), data)
        # Should be forbidden
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        # Change should not have been made
        self.assertEqual(Course.objects.get(pk=self.course.pk).region, old_region)

    def test_nulling_organizer_makes_requesting_user_organizer(self):
        course_id = self.course.id
        self.client.force_authenticate(self.staff)
        data = {
            'organizer': None
        }
        response = self.client.patch(reverse('course-detail', args=[self.course.id]), data, format='json')
        updated_course = Course.objects.get(id=course_id)
        self.assertEqual(updated_course.organizer, self.staff)
