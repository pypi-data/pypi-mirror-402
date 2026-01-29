import logging

from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import ListModelMixin
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from whitebox import import_whitebox_model, get_plugin_logger
from .models import (
    FlightSession,
)
from .serializers import (
    FlightSessionSerializer,
)
from .utils import query_for_airports


Location = import_whitebox_model("location.Location")


logger = get_plugin_logger(__name__)


class FlightSessionViewSet(GenericViewSet, ListModelMixin):
    # Sort flight sessions in timestamp-descending order, and key moments in
    # timestamp-ascending order for easier readability
    queryset = FlightSession.objects.prefetch_related(
        "recordings", "key_moments"
    ).order_by("-started_at")
    serializer_class = FlightSessionSerializer


class AirportSearchView(APIView):
    """
    API endpoint to search for airports by name or ICAO code.

    Query parameters:
        q (str): Search query for airport name or ICAO code
        limit (int, optional): Maximum number of results to return (default: 20)

    Returns:
        List of airports matching the search query with simplified data structure:
        [
            {
                "name": "Airport Name",
                "icao": "ICAO",
                "coordinates": [longitude, latitude]
            },
            ...
        ]
    """

    def get(self, request):
        query = request.query_params.get("q", "").strip().lower()
        limit = int(request.query_params.get("limit", 20))

        if not query:
            return Response(
                {"error": "Query parameter 'q' is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if len(query) < 2:
            return Response(
                {"error": "Query must be at least 2 characters long"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Query airports using the utility function
        airports = query_for_airports(query)

        # Limit results
        airports = airports[:limit]

        # Transform to simplified format for frontend
        # while accounting for missing data.
        # Note: It was found that sometimes "icaoCode" field was missing.
        results = []
        for airport in airports:
            geometry = airport.get("geometry", {})
            coordinates = geometry.get("coordinates", [])

            results.append(
                {
                    "name": airport.get("name", ""),
                    "icao": airport.get("icaoCode", ""),
                    "coordinates": coordinates,
                }
            )

        return Response(results, status=status.HTTP_200_OK)
