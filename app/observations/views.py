import logging

from django.core.exceptions import ImproperlyConfigured
from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import LandslideObservation
from .prediction import predict_landslide
from .rag import RagConfigurationError, RagServiceError, ask_rag
from .serializers import LandslideObservationSerializer, SafetyQuestionSerializer


logger = logging.getLogger(__name__)


class PredictionModelUnavailable(APIException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = 'The landslide prediction model is not available.'
    default_code = 'prediction_model_unavailable'


class SafetyAssistantUnavailable(APIException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = 'The safety assistant is not available.'
    default_code = 'safety_assistant_unavailable'


class LandslideObservationViewSet(viewsets.ModelViewSet):
    queryset = LandslideObservation.objects.all()
    serializer_class = LandslideObservationSerializer

    def _predict(self, validated_data):
        try:
            return predict_landslide(validated_data)
        except ImproperlyConfigured as error:
            logger.exception('Could not load the landslide prediction model.')
            raise PredictionModelUnavailable(str(error)) from error

    def perform_create(self, serializer):
        prediction = self._predict(serializer.validated_data)
        serializer.save(**prediction)

    def perform_update(self, serializer):
        observation = {
            **serializer.instance.__dict__,
            **serializer.validated_data,
        }
        prediction = self._predict(observation)
        serializer.save(**prediction)


class SafetyAssistantView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SafetyQuestionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            result = ask_rag(serializer.validated_data['question'])
        except RagConfigurationError as error:
            logger.error('Safety assistant configuration error: %s', error)
            raise SafetyAssistantUnavailable(
                detail=str(error),
                code='safety_assistant_not_configured',
            ) from error
        except RagServiceError as error:
            logger.exception('Safety assistant service is unavailable.')
            raise SafetyAssistantUnavailable(
                detail=str(error),
                code='safety_assistant_unavailable',
            ) from error

        return Response(result, status=status.HTTP_200_OK)
