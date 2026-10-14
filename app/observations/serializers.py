from rest_framework import serializers

from .models import LandslideObservation


class SafetyQuestionSerializer(serializers.Serializer):
    question = serializers.CharField(
        min_length=3,
        max_length=1000,
        trim_whitespace=True,
    )


class LandslideObservationSerializer(serializers.ModelSerializer):
    class Meta:
        model = LandslideObservation
        fields = '__all__'
        read_only_fields = (
            'id',
            'created_at',
            'landslide_observed',
            'landslide_prediction',
            'landslide_probability',
        )
