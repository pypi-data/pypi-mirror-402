from django.urls import path
from rest_framework.routers import SimpleRouter

from .views import (
    FlightSessionViewSet,
    AirportSearchView,
)


app_name = "whitebox_plugin_flight_management"


router = SimpleRouter()


router.register(
    r"flight-sessions",
    FlightSessionViewSet,
    basename="flight-session",
)

urlpatterns = [
    path("airports/search/", AirportSearchView.as_view(), name="airport-search"),
] + router.urls
