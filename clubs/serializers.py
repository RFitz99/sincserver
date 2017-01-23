from rest_framework.serializers import ModelSerializer 

from clubs.models import Club, CommitteePosition, Region
from serializers import DynamicFieldsModelSerializer
from users.models import User

class RegionSerializer(ModelSerializer):
    class Meta:
        model = Region
        fields = ('name', 'id',)


class ClubSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = Club
        # This is the largest possible set of fields that we
        # can return. The subset of fields to be sent is decided
        # in ClubViewSet.
        fields = (
            'contact_email',
            'contact_name',
            'contact_phone',
            'creation_date',
            'description',
            'foundation_date',
            'id',
            'name',
            'last_modified',
            'location',
            'region',
            'training_times',
            'users',
        )

    # A serializer for members that offers a small subset of
    # user attributes
    class ClubMemberSerializer(ModelSerializer):
        class Meta:
            model = User
            fields = ('id', 'first_name', 'last_name', 'email',)

    users = ClubMemberSerializer(many=True, read_only=True)
    region = RegionSerializer(read_only=True)


class CommitteePositionSerializer(ModelSerializer):
    class Meta:
        model = CommitteePosition
        fields = ('role',)
