from django.test import TestCase
from unittest.mock import patch, MagicMock

from plugin.manager import plugin_manager


class TestWhiteboxPluginTrafficDisplay(TestCase):
    def setUp(self) -> None:
        self.plugin = next(
            (
                x
                for x in plugin_manager.whitebox_plugins
                if x.__class__.__name__ == "WhiteboxPluginTrafficDisplay"
            ),
            None,
        )
        return super().setUp()

    def test_plugin_loaded(self):
        self.assertIsNotNone(self.plugin)

    def test_plugin_name(self):
        self.assertEqual(self.plugin.name, "Traffic Display")

    def test_plugin_capabilities(self):
        self.assertIn("traffic", self.plugin.provides_capabilities)

    def test_plugin_url_map(self):
        self.assertIn("traffic.aircraft-lookup", self.plugin.plugin_url_map)


class TestAircraftLookupViewSet(TestCase):
    def test_icao_decimal_to_hex_conversion(self):
        icao_decimal = 5055096
        expected_hex = "4d2278"
        actual_hex = format(int(icao_decimal), "x").lower()
        self.assertEqual(actual_hex, expected_hex)

    def test_icao_hex_passthrough(self):
        icao_hex = "4d2278"
        # When input is not all digits, it should be treated as hex
        self.assertFalse(icao_hex.isdigit())
        self.assertEqual(icao_hex.lower(), "4d2278")

    @patch("whitebox_plugin_traffic_display.views.lookup_aircraft_by_icao24")
    def test_aircraft_lookup_endpoint_missing_param(self, mock_lookup):
        from rest_framework.test import APIClient

        client = APIClient()
        response = client.get(
            "/plugin-views/whitebox_plugin_traffic_display/aircraft/lookup/"
        )
        self.assertEqual(response.status_code, 400)

    @patch("whitebox_plugin_traffic_display.views.lookup_aircraft_by_icao24")
    def test_aircraft_lookup_endpoint_not_found(self, mock_lookup):
        mock_lookup.return_value = None

        from rest_framework.test import APIClient

        client = APIClient()
        response = client.get(
            "/plugin-views/whitebox_plugin_traffic_display/aircraft/lookup/",
            {"icao_addr": "123456"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["found"])
