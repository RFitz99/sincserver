from rest_framework.test import APITestCase

from users.models import User
from qualifications.models import Certificate, Qualification

# Create your tests here.
class QualificationTestCase(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(first_name='Joe', last_name='Bloggs')
        self.d1 = Certificate.objects.create(name='Trainee Diver')

    def test_receive_certificate(self):
        self.user.receive_certificate(self.d1)
        self.assertTrue(Qualification.objects.filter(user=self.user, certificate=self.d1).exists())
