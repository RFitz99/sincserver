from django.core.urlresolvers import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from clubs.models import Club
from courses.models import Course, CourseEnrolment
from qualifications.models import Certificate
from users.models import User

class CourseDetailTestCase(APITestCase):

    def setUp(self):
        # Create a cert for the course
        certificate = Certificate.objects.create(name='Trainee Diver')
        self.creator = User.objects.create_user('Course', 'Creator')
        self.organizer = User.objects.create_user('Course', 'Organizer')
        self.course = Course.objects.create(
            certificate=certificate,
            creator=self.creator,
            organizer=self.organizer
        )
        # Create a club with a DO who has detail privileges
        self.club = Club.objects.create(name='UCCSAC')
        self.do = User.objects.create_user('Dive', 'Officer', club=self.club)
        # Enrol a user on the course
        self.member = User.objects.create_user('Club', 'Member', club=self.club)
        CourseEnrolment.objects.create(user=self.member, course=self.course)

    ###########################################################################
    # The detail view of a course will contain
    # * its creator
    # 
    # It will not contain
    # * its enrolments; these must be retrieved with a separate API call.
    #
    # For these tests, we're authenticating as the administrator, to
    # evaluate the maximum level of detail available. Other users may
    # see fewer details.
    ###########################################################################

    def test_course_detail_contains_creator(self):
        admin = User.objects.create_user('Staff', 'Member', is_staff=True)
        self.client.force_authenticate(admin)
        response = self.client.get(reverse('course-detail', args=[self.course.id]))
        data = response.data
        keys = [k for k in data.keys()]
        self.assertIn('creator', keys,
                      'Course detail should return its creator')
        creator = data['creator']
        # We expect to see the critical contact-detail fields of the
        # course creator
        expected_fields = ['id', 'first_name', 'last_name', 'email']
        keys = [k for k in creator.keys()]
        # Check the fields that should be returned
        for field in expected_fields:
            self.assertIn(field, keys,
                          'Course detail should return creator field: "{}"'.format(field)
                         )
        # Check for fields that should not be returned
        for field in set(keys) - set(expected_fields):
            self.fail('Course detail should not return creator field: "{}"'.format(field))

    def test_course_detail_does_not_contain_enrolment_list(self):
        admin = User.objects.create_user('Staff', 'Member', is_staff=True)
        self.client.force_authenticate(admin)
        response = self.client.get(reverse('course-detail', args=[self.course.id]))
        data = response.data
        keys = [k for k in data.keys()]
        self.assertNotIn('courseenrolments', keys,
                      'Course detail shouldn\'t return list of enrolments')

    ###########################################################################
    # Administrators can view the details of a course, including the
    # list of users enrolled on it.
    ###########################################################################

    def test_admin_can_view_course_detail(self):
        admin = User.objects.create_user('Staff', 'Member', is_staff=True)
        self.client.force_authenticate(admin)
        response = self.client.get(reverse('course-detail', args=[self.course.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    ###########################################################################
    # The course creator and organizer can view the details of a course,
    # including the list of users enrolled on it.
    ###########################################################################

    def test_organizer_can_view_course_detail(self):
        self.client.force_authenticate(self.organizer)
        response = self.client.get(reverse('course-detail', args=[self.course.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_creator_can_view_course_detail(self):
        self.client.force_authenticate(self.creator)
        response = self.client.get(reverse('course-detail', args=[self.course.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    ###########################################################################
    # A Dive Officer can view the details of a course.
    # The detail view will not contain members of their club who are
    # enrolled on it (these are retrieved through a separate view).
    ###########################################################################

    def test_dive_officer_can_view_course_detail(self):
        self.client.force_authenticate(self.do)
        response = self.client.get(reverse('course-detail', args=[self.course.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_dive_officer_cannot_see_list_of_club_members_enrolled(self):
        self.client.force_authenticate(self.do)
        response = self.client.get(reverse('course-detail', args=[self.course.id]))
        data = response.data
        keys = [k for k in data.keys()]
        self.assertNotIn('courseenrolments', keys,
                      'Course detail shouldn\'t return list of enrolments')

    ###########################################################################
    # A user can view the details of a course, whether or not they are
    # enrolled on the course. If they are enrolled on the course, they
    # can see that they are enrolled. They cannot view the complete list
    # of users enrolled on the course.
    ###########################################################################

    def test_user_can_view_course_detail_when_enrolled(self):
        self.client.force_authenticate(self.member)
        response = self.client.get(reverse('course-detail', args=[self.course.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_cannot_see_that_other_users_are_enrolled(self):
        other_user = User.objects.create_user('Other', 'User')
        CourseEnrolment.objects.create(user=other_user, course=self.course)
        self.client.force_authenticate(self.member)
        response = self.client.get(reverse('course-detail', args=[self.course.id]))
        data = response.data
        keys = [k for k in data.keys()]
        self.assertNotIn('courseenrolments', keys,
                      'Course detail shouldn\'t return list of enrolments')

    def test_user_can_view_course_detail_when_not_enrolled(self):
        other_user = User.objects.create_user('Other', 'User')
        self.client.force_authenticate(self.member)
        response = self.client.get(reverse('course-detail', args=[self.course.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # We expect not to see a list of enrolments
        data = response.data
        keys = [k for k in data.keys()]
        self.assertNotIn('courseenrolments', keys,
                      'Course detail shouldn\'t return list of enrolments')

    ###########################################################################
    # An unauthenticated user cannot view the details of a course.
    ###########################################################################

    def test_unauthenticated_user_cannot_view_course_detail(self):
        response = self.client.get(reverse('course-detail', args=[self.course.id]))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
