from datetime import date

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext as _

from clubs.models import Club, CommitteePosition
from clubs import roles
from qualifications.models import Qualification
from users import choices

DECEMBER = 12
this_year = date.today().year # Get the current year
end_of_last_year = date(this_year, DECEMBER, 31)
end_of_next_year = date(this_year, DECEMBER, 31)
end_of_this_year = date(this_year, DECEMBER, 31)

class UserManager(BaseUserManager):
    def create_user(self, first_name, last_name, password=None, **kwargs):
        """
        Creates and saves a user with the given name and password and returns
        the User object.
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
        # TODO: We can ensure username=ID by saving twice, but it seems
        # inefficient. I *think* we can get a provisional ID by calling
        # the constructor; I'll look into it --sdob
        user.username = user.id
        user.save()
        return user

    def create_superuser(self, first_name, last_name, password, **kwargs):
        """
        Creates and saves a superuser with the given name and password
        and returns the User object.
        """
        # Create and save a standard user
        user = self.create_user(first_name, last_name, password)
        # Set the 'is_admin' flag
        user.is_admin = True
        # Save a second time
        user.save(using=self._db)
        return user


class User(AbstractUser):

    # We have to declare a custom manager because we're using a non-standard
    # create_user method
    objects = UserManager()

    REQUIRED_FIELDS = ['first_name', 'last_name', 'email']

    # Title by which the user is to be addressed ('Dr', 'Ms', etc.)
    title = models.IntegerField(choices=choices.TITLE_CHOICES, blank=True, null=True)

    # Name fields. First name and surname are stored separately because
    # that's the way COMS does it. Setting max_length to 100 means that
    # we'll probably never have to worry about the length on either field.
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)

    # Gender; choices are retrieved from choices.py
    gender = models.IntegerField(choices=choices.GENDER_CHOICES, blank=True, null=True)

    # Date of birth
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

    # Next-of-kin information
    next_of_kin_name = models.CharField(max_length=100, blank=True, null=True, verbose_name=_('Next of kin'))
    next_of_kin_phone = models.CharField(max_length=50, blank=True, null=True, verbose_name=_('Next of kin phone'))

    ############################################################################
    # Club membership
    ############################################################################

    # Each user belongs to a club (including the default National club)
    club = models.ForeignKey(Club, blank=True, null=True)

    member_since = models.DateTimeField(default=timezone.now)

    ############################################################################
    # CFT administration stuff
    ############################################################################

    # CFT membership type: student/full.
    membership_type = models.IntegerField(choices=choices.MEMBERSHIP_CHOICES, default=choices.MEMBERSHIP_FULL)

    ############################################################################
    # Membership status
    ############################################################################

    def has_current_medical_disclaimer(self):
        """
        Check the user's history of medical disclaimers and determine
        whether they are currently covered by one.
        """
        # TODO: Implement this
        return True

    def is_currently_fit_to_dive(self):
        """
        Check whether the user has passed a fitness test recently enough to
        be fit to dive.
        """
        # TODO: Implement this
        return True

    def has_current_medical_assessment(self):
        """
        Check whether the user has a medical assessment that covers them
        """

        return True

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
        # from October to the following December.
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
    # Committee role setters ('become_$ROLE') and getters ('is_$ROLE')
    ############################################################################
    def __adopt_role(self, role):
        CommitteePosition.objects.get_or_create(user=self, club=self.club, role=role)

    def become_dive_officer(self):
        self.__adopt_role(roles.DIVE_OFFICER)

    def become_treasurer(self):
        self.__adopt_role(roles.TREASURER)

    def become_training_officer(self):
        self.__adopt_role(roles.TRAINING_OFFICER)

    # TODO: Finish these 'become_$ROLE' methods for the other committee roles

    def __has_role(self, role):
        return CommitteePosition.objects.filter(user=self, role=role).exists()

    def has_any_role(self):
        return CommitteePosition.objects.filter(user=self).exists()

    def is_dive_officer(self):
        return self.__has_role(roles.DIVE_OFFICER)

    def is_treasurer(self):
        return self.__has_role(roles.TREASURER)

    def is_training_officer(self):
        return self.__has_role(roles.TRAINING_OFFICER)

    # TODO: Finish these 'is_$ROLE' methods for the other committee roles


        ############################################################################
        # Convenience methods
        ############################################################################

    def readable_committee_positions(self):
        """
        Return a human-readable list of this user's committee positions.
        """
        return [position.get_role_display() for position in self.committee_positions.all()]

    def readable_membership_type(self):
        return self.get_membership_type_display()


    ############################################################################
    # Certificate handling
    ############################################################################

    def receive_certificate(self, certificate, date_granted=None):
        """
        Grant a certificate to the user.
        """
        if date_granted is not None:
            Qualification.objects.create(user=self, certificate=certificate, date_granted=date_granted)
        else:
            Qualification.objects.create(user=self, certificate=certificate)

    def lose_certificate(self, certificate):
        Qualification.objects.filter(user=self, certificate=certificate).delete()


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
