from django.core.urlresolvers import reverse
from rest_framework.test import APIRequestFactory, APITestCase

from clubs.models import Club
from permissions.permissions import IsAdminOrDiveOfficer
from users.models import User

class IsAdminOrDiveOfficerTestCase(APITestCase):

    def setUp(self):
        club = Club.objects.create(name='UCC')
        self.do = User.objects.create_user(first_name='Joe', last_name='Bloggs', club=club)
        self.do.become_dive_officer()

        self.staff = User.objects.create_user(first_name='Staff', last_name='Member')
        self.staff.is_staff = True
        self.staff.save()
        self.superuser = User.objects.create_superuser(first_name='Super', last_name='User', password='password')

    def test_dive_officer_passes(self):
        factory = APIRequestFactory()
        request = factory.get(reverse('user-list'))
        request.user = self.do
        self.assertTrue(IsAdminOrDiveOfficer().has_permission(request, None))

    def test_staff_passes(self):
        factory = APIRequestFactory()
        request = factory.get(reverse('user-list'))
        request.user = self.staff
        self.assertTrue(IsAdminOrDiveOfficer().has_permission(request, None))

    def test_superuser_passes(self):
        factory = APIRequestFactory()
        request = factory.get(reverse('user-list'))
        request.user = self.superuser
        self.assertTrue(IsAdminOrDiveOfficer().has_permission(request, None))

