from rest_framework import serializers
from clubs.serializers import ClubSerializer
from users.models import User
from serializers import DynamicFieldsModelSerializer

class UserSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = User
        # Begin with a permissive set of fields; this is
        # OK because we're specifically requesting them
        # in our views
        fields = (
            'id', 'first_name', 'last_name', 'gender',
            'title',
            'readable_committee_positions',
            'readable_membership_type',
            'date_of_birth',
            'email', 'phone_home', 'phone_mobile',
            'club',
            'current_membership_status',
            'is_staff',
            'member_since',
            'next_fitness_test_due_date',
            'next_medical_disclaimer_due_date',
            'next_medical_assessment_due_date',
            'next_renewal_due_date',
            'next_year_membership_status',
        )

    # We handle club assignment in the view, so the serializer can treat
    # it as read-only
    club = ClubSerializer(read_only=True)

    # Let the frontend know if the user is a staff member so that they
    # can view the admin options
    is_staff = serializers.ReadOnlyField()
