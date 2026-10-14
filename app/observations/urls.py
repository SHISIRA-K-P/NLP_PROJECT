from rest_framework.routers import DefaultRouter

from .views import LandslideObservationViewSet

router = DefaultRouter()
router.register('', LandslideObservationViewSet, basename='observation')

urlpatterns = router.urls
