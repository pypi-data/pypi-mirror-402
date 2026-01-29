import whitebox


class WhiteboxPluginTrafficDisplay(whitebox.Plugin):
    name = "Traffic Display"

    provides_capabilities = ["traffic"]
    slot_component_map = {
        "traffic.markers": "TrafficMarkers",
        "traffic.unknown-traffic-overlay": "UnknownTraffic",
    }
    exposed_component_map = {
        "service-component": {
            "traffic-service": "TrafficDisplayServiceComponent",
        },
        "map-layer": {
            "traffic-path": "map_layers/TrafficFlightPath",
        },
    }
    state_store_map = {
        "traffic": "stores/traffic",
    }
    plugin_url_map = {
        "traffic.aircraft-lookup": "whitebox_plugin_traffic_display:aircraft-lookup-list",
    }


plugin_class = WhiteboxPluginTrafficDisplay
