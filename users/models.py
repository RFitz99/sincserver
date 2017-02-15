from datetime import date

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext as _

from clubs.models import Club, CommitteePosition, Region
from clubs import roles
from qualifications.models import Qualification
from users import choices

# Date-related stuff; for computing a user's current membership status,
# we need to know where we are relative to the end of last year, this year,
# and next year
DECEMBER = 12
this_year = date.today().year # Get the current year
end_of_last_year = date(this_year, DECEMBER, 31)
end_of_next_year = date(this_year, DECEMBER, 31)
end_of_this_year = date(this_year, DECEMBER, 31)

def get_national_club():
    return Club.objects.get_or_create(
        name='National',
        region=Region.objects.get_or_create(name='National')[0]
    )[0]

# Because we're using a custom User model (rather than Django's built-in
# model), we also need to define a user manager with custom create_user()
# and create_superuser() methods. This is largely because we're using the
# user's CFT ID as their username for logging in, so we need to be able to
# create a User object without giving a username.
#
# The job of giving the user a username the same as their ID is handled
# by a signal (defined at the bottom of this file).
class UserManager(BaseUserManager):
    def create_user(self, first_name, last_name, password=None, **kwargs):
        """
        Creates and saves a user with the given name and password and returns
        the User object. The user will have their username assigned to their
        database ID in a post-save signal (defined in this file).
        """
        if not first_name and last_name:
            raise ValueError('Users must have a first and last name')

        user = self.model(
            first_name=first_name,
            last_name=last_name,
            **kwargs
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, first_name, last_name, password, **kwargs):
        """
        Creates and saves a superuser with the given name and password
        and returns the User object.
        """
        # Create and save a standard user
        user = self.create_user(first_name, last_name, password)
        # Set the 'is_superuser' and 'is_staff' flag
        user.is_superuser = True
        user.is_staff = True
        # Save a second time
        user.save(using=self._db)
        return user

# Here's our custom User model. We define quite a lot of fields on it,
# as well as various convenience methods that allow us to query a member's
# IUC-specific status with ease. We could have done this differently,
# by assigning a one-to-one Profile model to each user (as the Django docs
# recommend), but that would require us to access the user's profile
# every time we wanted to know anything about the user that wasn't
# directly related to authentication.
class User(AbstractUser):

    # We're using the custom manager, defined above.
    objects = UserManager()

    REQUIRED_FIELDS = ['first_name', 'last_name', 'email']

    # Title by which the user is to be addressed ('Dr', 'Ms', etc.).
    title = models.IntegerField(choices=choices.TITLE_CHOICES, blank=True, null=True)

    # Name fields. First name and surname are stored separately because
    # that's the way COMS does it. Setting max_length to 100 means that
    # we'll probably never have to worry about the length on either field.
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)

    # Gender; choices are retrieved from choices.py (so that they're
    # reusable).
    gender = models.IntegerField(choices=choices.GENDER_CHOICES, blank=True, null=True)

    # Date of birth.
    date_of_birth = models.DateField(blank=True, null=True)

    ############################################################################
    # Contact details
    ############################################################################

    # Email address. Django will handle the validation for us.
    email = models.EmailField()

    # Phone numbers. We're simply going to store these as strings, rather
    # than attempting to do validation ourselves. Down the line, if something
    # like libphonenumber turns out to be necessary, we can use it.
    phone_home = models.CharField(max_length=50, blank=True, verbose_name=_('Phone(home)'))
    phone_mobile = models.CharField(max_length=50, blank=True, verbose_name=_('Phone(mobile)'))

    # Next-of-kin information. Again, just strings.
    next_of_kin_name = models.CharField(max_length=100, blank=True, null=True, verbose_name=_('Next of kin'))
    next_of_kin_phone = models.CharField(max_length=50, blank=True, null=True, verbose_name=_('Next of kin phone'))

    ############################################################################
    # Club membership
    ############################################################################

    # Each user belongs to exactly one club (including the default National
    # club).
    club = models.ForeignKey(Club, blank=True, null=True, related_name='users',
                             on_delete=models.SET(get_national_club))

    # By default, a person has been a member of IUC since their User
    # object was created, but that won't be the case for anybody whose
    # details are transferred over from COMS.
    member_since = models.DateTimeField(default=timezone.now)

    ############################################################################
    # CFT administration stuff
    ############################################################################

    # CFT membership type: student/full.
    membership_type = models.IntegerField(choices=choices.MEMBERSHIP_CHOICES, default=choices.MEMBERSHIP_FULL)

    ############################################################################
    # Convenience methods for permisson handling
    ############################################################################

    # Is the user an admin?
    def is_admin(self):
        return self.is_staff or self.is_superuser

    ############################################################################
    # Membership status
    ############################################################################

    # Does the user have a current medical disclaimer?
    def has_current_medical_disclaimer(self):
        """
        Check the user's history of medical disclaimers and determine
        whether they are currently covered by one.
        """
        # TODO: Implement this
        return True

    # Is the user fit to dive?
    def is_currently_fit_to_dive(self):
        """
        Check whether the user has passed a fitness test recently enough to
        be fit to dive.
        """
        # TODO: Implement this
        return True

    # Has the user got an in-date medical assessment?
    def has_current_medical_assessment(self):
        """
        Check whether the user has a medical assessment that covers them
        """

        return True

    # Look at the state of the user's disclaimer, assessment, and
    # fit-to-dive status, and decide whether they're current or lapsed.
    def current_membership_status(self):
        """
        Return the user's diving status. A user is current if they satisfy
        all of the following conditions:
            (a) they have a current medical disclaimer;
            (b) they have passed a fitness test in date; and 
            (c) they have been assessed as medically fit recently (according
            to CFT rules).
        Otherwise, the user is lapsed.
        """
        disclaimer = self.has_current_medical_disclaimer()
        fit_to_dive = self.is_currently_fit_to_dive()
        assessment = self.has_current_medical_assessment()
        if all([disclaimer, fit_to_dive, assessment]):
            return choices.STATUS_CURRENT
        return choices.STATUS_LAPSED


        ############################################################################
        # Methods to calculate various important dates
        # TODO: These are currently not accurate, because the CFT year runs
        # from October to the following December. We'll need to come up
        # with some more sophisticated logic.
        ############################################################################

    def next_fitness_test_due_date(self):
        # TODO: Compute actual logic for this based on CFT rules.
        if self.is_currently_fit_to_dive():
            return end_of_this_year
        return end_of_last_year

    def next_medical_disclaimer_due_date(self):
        if self.has_current_medical_disclaimer():
            return end_of_this_year
        return end_of_last_year

    def next_medical_assessment_due_date(self):
        if self.has_current_medical_assessment():
            return end_of_this_year
        return end_of_last_year

    def next_renewal_due_date(self):
        # TODO: this is just a placeholder
        return end_of_this_year

    def next_year_membership_status(self):
        # TODO: fix this
        return 'LAPSED'


    ############################################################################
    # Higher-echelon role methods
    ############################################################################

    # Is this user the dive club of any region?
    def is_regional_dive_officer(self):
        return any([region.dive_officer == self for region in Region.objects.all()])

    ############################################################################
    # Club committee role setters ('become_$ROLE') and getters ('is_$ROLE')
    ############################################################################

    # Generic method for assigning a committee role to a user
    def __adopt_role(self, role):
        CommitteePosition.objects.get_or_create(user=self, club=self.club, role=role)

    # Make this user the Dive Officer of their club.
    def become_dive_officer(self):
        self.__adopt_role(roles.DIVE_OFFICER)

    # Make this user the treasurer of their club.
    def become_treasurer(self):
        self.__adopt_role(roles.TREASURER)

    # Make this user the treasurer of their club.
    def become_training_officer(self):
        self.__adopt_role(roles.TRAINING_OFFICER)

    # TODO: Finish these 'become_$ROLE' methods for the other committee roles

    # Generic method to check whether a user holds a committee role.
    def __has_role(self, role):
        return CommitteePosition.objects.filter(user=self, role=role).exists()

    # Has the user got *any* committee role at all?
    def has_any_role(self):
        return CommitteePosition.objects.filter(user=self).exists()

    # Is the user a Dive Officer?
    def is_dive_officer(self):
        return self.__has_role(roles.DIVE_OFFICER)

    # Is the user a treasurer?
    def is_treasurer(self):
        return self.__has_role(roles.TREASURER)

    # Is the user a training officer?
    def is_training_officer(self):
        return self.__has_role(roles.TRAINING_OFFICER)

    # TODO: Finish these 'is_$ROLE' methods for the other committee roles


        ############################################################################
        # Convenience methods
        ############################################################################

    # Return a human-readable (English) list of the user's committee positions.
    def readable_committee_positions(self):
        """
        Return a human-readable list of this user's committee positions.
        """
        return [position.get_role_display() for position in self.committee_positions.all()]

    # Return a human-readable (English) description of the user's membership
    # type.
    def readable_membership_type(self):
        return self.get_membership_type_display()


    ############################################################################
    # Instructional certification checking
    ############################################################################

    # Does the user hold an instructor-level grade?
    def is_instructor(self):
        return self.qualifications.filter(certificate__is_instructor_certificate=True).exists()

    ############################################################################
    # Certificate handling
    ############################################################################

    # Give this user the specified certificate. Optionally, specify the
    # date on which they were granted the cert.
    def receive_certificate(self, certificate, date_granted=None):
        """
        Grant a certificate to the user.
        """
        if date_granted is not None:
            Qualification.objects.create(user=self, certificate=certificate, date_granted=date_granted)
        else:
            Qualification.objects.create(user=self, certificate=certificate)

    # Revoke the specified certificate from this user. (I don't know why
    # you would want to do this...)
    def lose_certificate(self, certificate):
        Qualification.objects.filter(user=self, certificate=certificate).delete()


    ############################################################################
    # Authority checking --- is this user under the authority of another?
    ############################################################################

    def has_as_dive_officer(self, other_user):
        # True if both users are in the same club and the other user is
        # the Dive Officer, otherwise False
        return self.club == other_user.club and other_user.is_dive_officer()


    ############################################################################
    # Implementation details (basically boilerplate stuff required by Django)
    ############################################################################

    def get_full_name(self):
        """
        Return a long formal, human-readable identifier for the user.
        """
        return '{0.first_name} {0.last_name}'.format(self)

    def get_short_name(self):
        """
        Return a brief, human-readable identifier for the user.
        """
        return self.first_name

    def __str__(self):
        # This is principally used in the shell and isn't particularly
        # useful for 
        return '{} (CFT #{})'.format(self.get_full_name(), self.id)

###############################################################################
# Database signals.
###############################################################################


# When a User object is created, set their username to their ID and save
# the object again.
def set_username(sender, **kwargs):
    user = kwargs['instance']
    if kwargs['created']:
        user.username = user.id
        user.save()
models.signals.post_save.connect(set_username, User)
