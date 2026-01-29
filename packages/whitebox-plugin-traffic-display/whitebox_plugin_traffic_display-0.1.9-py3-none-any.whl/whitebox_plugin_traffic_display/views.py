import logging

from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import status

from .utils import lookup_aircraft_by_icao24, lookup_aircraft_type


logger = logging.getLogger(__name__)


class AircraftLookupViewSet(ViewSet):
    def list(self, request):
        """
        Lookup aircraft information by ICAO24 address.

        Parameters:
            icao_addr: ICAO24 address in decimal or hex format

        Returns:
            Aircraft info with resolved type info if available.
        """
        icao_addr = request.query_params.get("icao_addr", "").strip()

        if not icao_addr:
            return Response(
                {"error": "Query parameter 'icao_addr' is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Convert decimal to hex if needed
        try:
            if icao_addr.isdigit():
                icao24_hex = format(int(icao_addr), "x").lower()
            else:
                icao24_hex = icao_addr.lower()
        except ValueError:
            return Response(
                {"error": "Invalid icao_addr format"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        aircraft = lookup_aircraft_by_icao24(icao24_hex)
        if not aircraft:
            return Response({"found": False, "icao24": icao24_hex})

        typecode = aircraft.get("typecode")
        type_info = lookup_aircraft_type(typecode) if typecode else None

        return Response(
            {
                "found": True,
                "icao24": icao24_hex,
                "aircraft": aircraft,
                "type_info": type_info,
            }
        )
