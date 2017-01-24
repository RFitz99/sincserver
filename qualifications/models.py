import datetime
from django.utils import timezone

from django.db import models

class Certificate(models.Model):

    class Meta:
        ordering = ('name',)

    # The name of this certificate
    name = models.CharField(max_length=200)

    # Is this a certificate that entitles the user to instruct other
    # members?
    is_instructor_certificate = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class Qualification(models.Model):
    """
    Intermediate model for the granting of certificates
    """

    # Which certificate?
    certificate = models.ForeignKey('Certificate', on_delete=models.CASCADE)

    # Granted to whom?
    user = models.ForeignKey('users.User', related_name='qualifications', on_delete=models.CASCADE)

    # When was it granted? By default, when the model is created
    date_granted = models.DateField(blank=True, default=datetime.date.today)

    # Internal use
    date_created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return '{}: {} ({})'.format(self.user, self.certificate, self.date_granted.strftime('%d/%m/%Y'))
