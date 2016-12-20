from rest_framework.serializers import ModelSerializer

from clubs.models import CommitteePosition, Region

class CommitteePositionSerializer(ModelSerializer):
    class Meta:
        model = CommitteePosition
        fields = ('role',)


class RegionSerializer(ModelSerializer):
    class Meta:
        model = Region
        fields = ('name', 'id',)
