from django.core.urlresolvers import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from clubs.models import Club, Region
from courses.models import Course, CourseEnrolment
from qualifications.models import Certificate
from users.models import User

class CoursesOrganizedTestCase(APITestCase):
    def setUp(self):
        # A staff member who'll create courses
        self.staff = User.objects.create_user('Staff', 'Member', is_staff=True)
        # Create a club, a user, and a course that they're organizing
        region = Region.objects.create(name='South')
        self.club = Club.objects.create(name='UCCSAC', region=region)
        self.user = User.objects.create_user('Club', 'Member', club=self.club)
        self.course = Course.objects.create(
            certificate=Certificate.objects.create(name='Trainee Diver'),
            creator=self.staff,
            organizer=self.user,
            region=region,
        )

    ###########################################################################
    # Our assumptions for viewing courses by user:
    # 1. An admin should be able to view the courses any user is organizing.
    # 2. A DO should be able to view the courses a member of their club
    #    is organizing, but not the courses a non-member is organizing.
    # 3. A user should be able to view only the courses they have organized.
    # 4. An unauthenticated user should not be able to view the courses
    #    a user is organizing.
    ###########################################################################

    def test_admin_can_view_courses_a_user_has_organized(self):
        self.client.force_authenticate(self.staff)
        response = self.client.get(reverse('user-courses-organized-list', args=[self.user.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                        'Admin should be able to view courses a user organized')

    def test_do_can_view_courses_a_club_member_has_organized(self):
        do = User.objects.create_user('Dive', 'Officer', club=self.club)
        do.become_dive_officer()
        self.client.force_authenticate(do)
        response = self.client.get(reverse('user-courses-organized-list', args=[self.user.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                        'DO should be able to view courses a member organized')

    def test_do_cannot_view_courses_a_non_member_has_organized(self):
        do = User.objects.create_user('Dive', 'Officer', club=Club.objects.create(name='CSAC'))
        do.become_dive_officer()
        self.client.force_authenticate(do)
        response = self.client.get(reverse('user-courses-organized-list', args=[self.user.id]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND,
                        'DO should not be able to view courses a non-member organized')

    def test_user_can_view_courses_they_have_organized(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse('user-courses-organized-list', args=[self.user.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                        'User should be able to view courses they organized')

    def test_user_cannot_view_courses_another_user_has_organized(self):
        self.client.force_authenticate(User.objects.create_user('Another', 'User'))
        response = self.client.get(reverse('user-courses-organized-list', args=[self.user.id]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND,
                        'User shouldn\'t be able to view courses another user organized')

    def test_unauthenticated_user_cannot_view_courses_a_user_has_organized(self):
        response = self.client.get(reverse('user-courses-organized-list', args=[self.user.id]))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
