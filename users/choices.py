from django.utils.translation import ugettext as _

# Some of the attributes of the User object are defined to be one of
# a fixed set of choices. We don't expect the number of different
# possible titles to change very often, for example. Internally, we're
# storing these fields as integers. This file defines the possible
# fixed choices that each attribute can take. They're tuples of tuples,
# where the second member of each tuple is a human-readable name for the
# value.

# Genders. Currently binary.
GENDER_CHOICES = (
    (0, _('Female')),
    (1, _('Male')),
)

# Titles. This is the same set of titles used in COMS.
TITLE_CHOICES = (
    (0, _('Dr')),
    (1, _('Miss')),
    (2, _('Mr')),
    (3, _('Mrs')),
    (4, _('Ms')),
)

# Membership types. Members can be 'full' or 'student' divers; this
# determines the annual membership fee that they pay.
MEMBERSHIP_FULL = 0
MEMBERSHIP_STUDENT = 1

MEMBERSHIP_CHOICES = (
    (MEMBERSHIP_STUDENT, _('Student Diver')),
    (MEMBERSHIP_FULL, _('Full Diver')),
)

# Current membership status; this one is a string. We don't actually
# store this in the database; instead, we compute a user's membership
# status based on the criteria that determine it (medical assessment,
# fitness to dive, etc.) and represent it using this value.
STATUS_CURRENT = 'Current'
STATUS_LAPSED = 'Lapsed'
