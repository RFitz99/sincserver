from rest_framework.test import APITestCase
from users.models import User

class SimpleUserTestCase(APITestCase):

    def setUp(self):
        self.u = User.objects.create_user(first_name='Joe', last_name='Bloggs')

    def test_everything_is_configured_properly(self):
        """
        Just creates a user and checks that it exists.
        """
        self.assertTrue(User.objects.filter(pk=self.u.id).exists())
        user = User.objects.get(pk=self.u.id)
        self.assertEquals('Joe', user.first_name)
        self.assertEquals('Bloggs', user.last_name)
        self.assertEquals('Joe Bloggs', user.get_full_name())

    def test_creating_with_optional_fields(self):
        email = 'joeblow@example.com'
        u = User.objects.create_user(first_name='Joe', last_name='Bloggs', email=email)
        self.assertTrue(User.objects.filter(email=email).exists())

    def test_username_equals_id(self):
        self.assertEquals(self.u.username, self.u.id)

    def test_get_full_name(self):
        self.assertEquals('Joe Bloggs', self.u.get_full_name())
