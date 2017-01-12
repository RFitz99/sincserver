from django.db import models

from clubs.models import Region
from qualifications.models import Certificate
from users.models import User

class Course(models.Model):

    # What qualification does this course confer?
    certificate = models.ForeignKey(Certificate)

    # Do we send out materials for this course?
    send_out_materials = models.BooleanField(default=False)

    # TODO: add applicants

    # Who created this?
    creator = models.ForeignKey(User, related_name="created_courses")

    # Who's organizing it?
    organizer = models.ForeignKey(User, related_name="organized_courses")

    # Organizational details
    location = models.TextField(blank=True, null=True)

    # When is this on? It can be blank, in which case there's no cutoff
    datetime = models.DateTimeField(blank=True, null=True)

    # Maximum number of participants; can be blank, in which case there's
    # no limit
    maximum_participants = models.PositiveIntegerField(blank=True, null=True)

    # The region in which the course is being held; this may not be the
    # same as the organizer or the creator's region
    region = models.ForeignKey('clubs.Region', blank=True, null=True)

    # Who's teaching this?
    instructors = models.ManyToManyField(User, through='courses.CourseInstruction', related_name='courses_instructed')

    # Who's attending
    students = models.ManyToManyField(User, through='courses.CourseEnrolment', related_name='courses_enrolled')

    ############################################################################
    # Internal use
    ############################################################################
    date_created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)



class CourseEnrolment(models.Model):

    # Foreign keys to the member and course
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)

    # Has the member's Dive Officer checked this?
    recommended_by_dive_officer = models.BooleanField(blank=True, default=False)

    ############################################################################
    # Internal use
    ############################################################################
    date_created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)


class CourseInstruction(models.Model):
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)

    expense_type = models.CharField(max_length=200, blank=True, null=True)
    expense_value = models.PositiveIntegerField(blank=True, default=0)

    ############################################################################
    # Internal use
    ############################################################################
    date_created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)
