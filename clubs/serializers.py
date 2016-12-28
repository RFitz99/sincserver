from rest_framework.serializers import ModelSerializer

from clubs.models import Club, CommitteePosition, Region

class ClubSerializer(ModelSerializer):
    class Meta:
        model = Club
        fields = ('name', 'id',)

class CommitteePositionSerializer(ModelSerializer):
    class Meta:
        model = CommitteePosition
        fields = ('role',)


class RegionSerializer(ModelSerializer):
    class Meta:
        model = Region
        fields = ('name', 'id',)
