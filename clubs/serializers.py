from rest_framework.serializers import ModelSerializer 

from clubs.models import Club, CommitteePosition, Region
from users.models import User

class RegionSerializer(ModelSerializer):
    class Meta:
        model = Region
        fields = ('name', 'id',)


class ClubSerializer(ModelSerializer):
    class Meta:
        model = Club
        # This is the largest possible set of fields that we
        # can return. The subset of fields to be sent is decided
        # in ClubViewSet.
        fields = ('name', 'id', 'region', 'users', 'creation_date',
                  'foundation_date', 'last_modified',)

    # A serializer for members that offers a small subset of
    # user attributes
    class ClubMemberSerializer(ModelSerializer):
        class Meta:
            model = User
            fields = ('id', 'first_name', 'last_name', 'email',)

    users = ClubMemberSerializer(many=True, read_only=True)

    def __init__(self, *args, **kwargs):
        specified_fields = kwargs.pop('fields', None)
        super(ClubSerializer, self).__init__(*args, **kwargs)
        if specified_fields is not None:
            specified_fields = set(specified_fields)
            available_fields = set(self.fields.keys())
            for field_name in available_fields - specified_fields:
                self.fields.pop(field_name)

class CommitteePositionSerializer(ModelSerializer):
    class Meta:
        model = CommitteePosition
        fields = ('role',)
