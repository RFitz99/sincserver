from rest_framework.serializers import ModelSerializer 

from clubs.models import Club, CommitteePosition, Region

class RegionSerializer(ModelSerializer):
    class Meta:
        model = Region
        fields = ('name', 'id',)

class ClubSerializer(ModelSerializer):
    class Meta:
        model = Club
        fields = ('name', 'id', 'region',)
    #region = RegionSerializer(read_only=True)

class CommitteePositionSerializer(ModelSerializer):
    class Meta:
        model = CommitteePosition
        fields = ('role',)
