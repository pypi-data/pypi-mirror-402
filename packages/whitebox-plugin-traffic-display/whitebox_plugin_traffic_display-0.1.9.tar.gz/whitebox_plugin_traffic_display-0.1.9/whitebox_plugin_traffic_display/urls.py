from rest_framework.routers import SimpleRouter

from .views import AircraftLookupViewSet


app_name = "whitebox_plugin_traffic_display"


router = SimpleRouter()


router.register(
    r"aircraft/lookup",
    AircraftLookupViewSet,
    basename="aircraft-lookup",
)

urlpatterns = router.urls
