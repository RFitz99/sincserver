from django.utils.translation import ugettext as _


# These must be distinct

DIVE_OFFICER = 0
CAPTAIN = 1
TREASURER = 2
SECRETARY = 3
TRAINING_OFFICER = 4

ROLE_CHOICES = (
        (DIVE_OFFICER, _('Dive Officer')),
        (CAPTAIN, _('Captain')),
        (TREASURER, _('Treasurer')),
        (SECRETARY, _('Secretary')),
        (TRAINING_OFFICER, _('Training Officer')),
        )
