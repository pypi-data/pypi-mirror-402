import csv
import os

from django.conf import settings

AIRCRAFT_DATA_DIR = os.path.join(settings.MANAGED_ASSETS_ROOT, "aircraft_data")
OPENSKY_CSV = os.path.join(AIRCRAFT_DATA_DIR, "opensky_aircraft_database.csv")
AIRCRAFT_TYPES_CSV = os.path.join(AIRCRAFT_DATA_DIR, "aircraft_types.csv")


def lookup_aircraft_by_icao24(icao24_hex: str) -> dict | None:
    """
    Search OpenSky CSV for aircraft by ICAO24 hex address.

    Parameters:
        icao24_hex: ICAO24 address in hex format

    Returns:
        Aircraft info dict if found, else None.
    """
    if not os.path.exists(OPENSKY_CSV):
        return None

    icao24_hex = icao24_hex.lower()
    with open(OPENSKY_CSV, "r") as f:
        # OpenSky CSV uses single quotes as the quote character
        reader = csv.DictReader(f, quotechar="'")
        for row in reader:
            if row.get("icao24", "").lower() == icao24_hex:
                return row
    return None


def lookup_aircraft_type(typecode: str) -> dict | None:
    """
    Search aircraft types CSV for type info by ICAO typecode.

    Parameters:
        typecode: ICAO aircraft typecode

    Returns:
        Type info dict if found, else None.
    """
    if not os.path.exists(AIRCRAFT_TYPES_CSV):
        return None

    typecode = typecode.upper()
    with open(AIRCRAFT_TYPES_CSV, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("icao", "").upper() == typecode:
                return row
    return None
