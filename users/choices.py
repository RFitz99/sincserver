from django.utils.translation import ugettext as _

GENDER_CHOICES = (
    (0, _('Female')),
    (1, _('Male')),
)

TITLE_CHOICES = (
    (0, _('Dr')),
    (1, _('Miss')),
    (2, _('Mr')),
    (3, _('Mrs')),
    (4, _('Ms')),
)

MEMBERSHIP_FULL = 0
MEMBERSHIP_STUDENT = 1

MEMBERSHIP_CHOICES = (
    (MEMBERSHIP_STUDENT, _('Student Diver')),
    (MEMBERSHIP_FULL, _('Full Diver')),
)

STATUS_CURRENT = 'Current'
STATUS_LAPSED = 'Lapsed'
