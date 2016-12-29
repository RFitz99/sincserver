import uuid
from django.db import models

from clubs.roles import ROLE_CHOICES

# Create your models here.
class Club(models.Model):

    def __str__(self):
        return self.name

    ############################################################################
    # Internal details
    ############################################################################

    # ID and primary key
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    ############################################################################
    # Club details
    ############################################################################

    # The club's name
    name = models.CharField(max_length=200)

    # The club's region
    region = models.ForeignKey('Region', blank=True, null=True)

    # When the club was founded (almost certainly before the club was added
    # to the system
    foundation_date = models.DateField(blank=True, null=True)

    ############################################################################
    # Internal use only
    ############################################################################

    # This is for internal use only; we'll provide a separate field for when the club was
    # founded
    creation_date = models.DateTimeField(auto_now_add=True)

    # When was the record last modified?
    last_modified = models.DateTimeField(auto_now=True)


class ClubMembership(models.Model):
    """
    """
    pass


class CommitteePosition(models.Model):
    """
    A CommitteePosition connects three things:
    (1) a User,
    (2) a Club, and
    (3) a Role.
    """

    def __str__(self):
        return '{}, {} ({})'.format(self.user, self.role, self.club)

    user = models.ForeignKey('users.User', related_name='committee_positions')
    club = models.ForeignKey('Club')
    role = models.IntegerField(choices=ROLE_CHOICES)


class Region(models.Model):
    """
    A Region has a Dive Officer, and a name.
    """

    dive_officer = models.ForeignKey('users.User', blank=True, null=True)
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name
