from whitebox import Plugin
from .handlers import (
    FlightStartHandler,
    FlightEndHandler,
    KeyMomentRecordHandler,
    KeyMomentFinishHandler,
    KeyMomentUpdateHandler,
    KeyMomentDeleteHandler,
)
from .utils import download_airport_data


class WhiteboxPluginFlightManagement(Plugin):
    name = "Flight Management"

    provides_capabilities = [
        "flight-management",
    ]
    slot_component_map = {
        "flight-management.trigger-button": "TriggerButton",
        "flight-management.flight-plan-overlay": "FlightPlanOverlay",
    }
    exposed_component_map = {
        "service-component": {
            "flight-service": "FlightServiceComponent",
        },
        "flight-management": {
            "trigger-button": "TriggerButton",
            "flight-plan-overlay": "FlightPlanOverlay",
        },
    }

    plugin_event_map = {
        "flight.start": FlightStartHandler,
        "flight.end": FlightEndHandler,
        "flight.key_moment.record": KeyMomentRecordHandler,
        "flight.key_moment.finish": KeyMomentFinishHandler,
        "flight.key_moment.update": KeyMomentUpdateHandler,
        "flight.key_moment.delete": KeyMomentDeleteHandler,
    }

    state_store_map = {
        "flight.inputs": "stores/inputs",
        "flight.mission-control": "stores/mission_control",
        "flight.flight-plan": "stores/flight_plan",
    }

    plugin_url_map = {
        "flight.flight-session-list": "whitebox_plugin_flight_management:flight-session-list",
        "flight.airport-search": "whitebox_plugin_flight_management:airport-search",
    }

    def get_plugin_classes_map(self):
        from .services import FlightService
        from .serializers import (
            FlightSessionSerializer,
            KeyMomentSerializer,
        )

        return {
            "flight.FlightService": FlightService,
            "flight.FlightSessionSerializer": FlightSessionSerializer,
            "flight.KeyMomentSerializer": KeyMomentSerializer,
        }

    def on_load(self):
        download_airport_data()


plugin_class = WhiteboxPluginFlightManagement
