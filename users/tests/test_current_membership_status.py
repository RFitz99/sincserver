from django.core.urlresolvers import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from users.models import User

class CurrentMembershipStatusTestCase(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user('Nosmo', 'King')

    def test_user_can_view_current_membership_status(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse('user-current-membership-status', args=[self.user.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
