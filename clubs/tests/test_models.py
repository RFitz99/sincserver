from rest_framework.test import APITestCase

from clubs.models import Club, CommitteePosition
from clubs.roles import DIVE_OFFICER, ROLE_CHOICES
from users.models import User

class ClubModelTestCase(APITestCase):

    # Just simple tests to push up coverage...
    
    def test_club_str(self):
        name = 'Aé—'
        club = Club.objects.create(name=name)
        self.assertEqual(name, club.name)


class CommitteePositionTestCase(APITestCase):

    def test_committee_position_str(self):
        club_name = 'UCCSAC'
        club = Club.objects.create(name='UCCSAC')

        user_first_name = 'Joe'
        user_last_name = 'Bloggs'
        user = User.objects.create_user('Joe', 'Bloggs', club=club)
        user_id = user.id

        expected_string = 'Joe Bloggs (CFT #{}), Dive Officer (UCCSAC)'.format(user_id)

        cp = CommitteePosition.objects.create(user=user, club=club, role=DIVE_OFFICER)
        self.assertEqual(cp.__str__(), expected_string)
