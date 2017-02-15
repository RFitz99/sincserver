import uuid
from django.db import models

from clubs.roles import ROLE_CHOICES

def get_national_region():
    return Region.objects.get_or_create(name='National')[0]

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
    region = models.ForeignKey('Region', blank=True, null=True,
                              on_delete=models.SET(get_national_region))

    # When the club was founded (almost certainly before the club was added
    # to the system
    foundation_date = models.DateField(blank=True, null=True)

    # A free-form textual description of the club
    description = models.TextField(blank=True, null=True)

    # A contact name; not necessarily a specific club member
    contact_name = models.CharField(max_length=100, blank=True, null=True)

    # A contact email; not necessarily a specific club member
    contact_email = models.EmailField(blank=True, null=True)

    # A contact phone number; not necessarily a specific club member
    contact_phone = models.CharField(max_length=100, blank=True, null=True)

    # A location; a free-form textual description (since it's purely
    # informational and intended to be consumed by humans)
    location = models.TextField(blank=True, null=True)

    # Training times; a free-form textual description (since it's purely
    # informational and intended to be consumed by humans)
    training_times = models.TextField(blank=True, null=True)


    ############################################################################
    # Authority checking --- is this club DO'd by a user
    ############################################################################

    def has_as_dive_officer(self, user):
        return user.club == self and user.is_dive_officer()

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
        return '{}, {} ({})'.format(self.user, self.get_role_display(), self.club)

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
