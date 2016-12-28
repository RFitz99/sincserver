from rest_framework import serializers
from clubs.serializers import ClubSerializer
from users.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        # Begin with a permissive set of fields; this is
        # OK because we're specifically requesting them
        # in our views
        fields = (
            'id', 'first_name', 'last_name', 'gender',
            'readable_committee_positions',
            'readable_membership_type',
            'date_of_birth',
            'email', 'phone_home', 'phone_mobile',
            'club',
            'current_membership_status',
            'member_since',
            'next_fitness_test_due_date',
            'next_medical_disclaimer_due_date',
            'next_medical_assessment_due_date',
            'next_renewal_due_date',
            'next_year_membership_status',
        )

    club = ClubSerializer()

    # Our constructor takes an optional 'fields' argument that allows us
    # to specify the fields that should be serialized. If a set of fields
    # is explicitly specified, then exclude unspecified fields; otherwise
    # send the default set.
    def __init__(self, *args, **kwargs):
        # Don't pass the 'fields' argument up to the parent constructor
        specified_fields = kwargs.pop('fields', None)
        # Instantiate the superclass
        super(UserSerializer, self).__init__(*args, **kwargs)
        # Drop any fields that aren't explicitly specified
        if specified_fields is not None:
            # Generate sets of strings so that we can diff them easily
            specified_fields = set(specified_fields)
            available_fields = set(self.fields.keys())
            for field_name in available_fields - specified_fields:
                self.fields.pop(field_name)
