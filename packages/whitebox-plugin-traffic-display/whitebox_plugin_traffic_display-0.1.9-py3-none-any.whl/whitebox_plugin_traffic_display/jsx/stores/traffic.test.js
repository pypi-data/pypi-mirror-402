import useTrafficStore, { getTrafficLabel } from "./traffic";

describe("useTrafficStore", () => {
  let originalDateNow;

  beforeEach(() => {
    // Reset store to initial state
    useTrafficStore.setState({
      staleTrafficTimeout: 1000 * 10,
      staleTrafficRemovalInterval: 1000 * 1,
      trafficData: [],
      trafficMarkers: {},
      aircraftCache: {},
    });

    // Mock Date.now for consistent testing
    originalDateNow = Date.now;
    Date.now = vi.fn(() => 1000000); // Fixed timestamp
  });

  afterEach(() => {
    Date.now = originalDateNow;
    vi.clearAllMocks();
  });

  describe("Initial State", () => {
    test("should have correct initial state", () => {
      const state = useTrafficStore.getState();

      expect(state.staleTrafficTimeout).toBe(10000);
      expect(state.staleTrafficRemovalInterval).toBe(1000);
      expect(state.trafficData).toEqual([]);
      expect(state.trafficMarkers).toEqual({});
    });

    test("should have all required methods", () => {
      const state = useTrafficStore.getState();

      expect(typeof state.addPositionsForEntities).toBe("function");
      expect(typeof state.removePositionsForEntities).toBe("function");
      expect(typeof state.addTrafficData).toBe("function");
      expect(typeof state.removeStaleTrafficData).toBe("function");
      expect(typeof state.renderTrafficData).toBe("function");
      expect(typeof state.updateTraffic).toBe("function");
      expect(typeof state.removeStaleTraffic).toBe("function");
      expect(typeof state.lookupAircraft).toBe("function");
      expect(typeof state.getAircraftFromCache).toBe("function");
    });
  });

  describe("getTrafficLabel Helper Function", () => {
    test("should create label with Tail callsign", () => {
      const traffic = {
        Tail: "N123AB",
        Alt: 35000,
        Speed: 450,
      };

      const label = getTrafficLabel(traffic);
      expect(label).toBe("N123AB\n35000ft @ 450kt");
    });

    test("should fallback to Reg when Tail not available", () => {
      const traffic = {
        Reg: "G-ABCD",
        Alt: 28000,
        Speed: 380,
      };

      const label = getTrafficLabel(traffic);
      expect(label).toBe("G-ABCD\n28000ft @ 380kt");
    });

    test("should fallback to Icao_addr when Tail and Reg not available", () => {
      const traffic = {
        Icao_addr: "ABC123",
        Alt: 15000,
        Speed: 250,
      };

      const label = getTrafficLabel(traffic);
      expect(label).toBe("ABC123\n15000ft @ 250kt");
    });

    test("should handle missing altitude and speed", () => {
      const traffic = {
        Tail: "N456CD",
      };

      const label = getTrafficLabel(traffic);
      expect(label).toBe("N456CD\nN/Aft @ N/Akt");
    });

    test("should handle zero values for altitude and speed", () => {
      const traffic = {
        Tail: "N789EF",
        Alt: 0,
        Speed: 0,
      };

      const label = getTrafficLabel(traffic);
      expect(label).toBe("N789EF\nN/Aft @ N/Akt");
    });

    test("should use enrichment data when provided", () => {
      const traffic = {
        Icao_addr: "ABC123",
        Tail: "CND127",
        Alt: 41000,
        Speed: 448,
      };
      const enrichment = {
        found: true,
        aircraft: {
          registration: "9H-TJD",
          operator: "Corendon Airlines",
          model: "737-86J",
        },
        type_info: {
          model: "Boeing 737-800",
        },
      };

      const label = getTrafficLabel(traffic, enrichment);
      expect(label).toContain("9H-TJD");
      expect(label).toContain("Boeing 737-800");
      expect(label).toContain("Corendon Airlines");
    });

    test("should fallback gracefully when enrichment not found", () => {
      const traffic = {
        Icao_addr: "123456",
        Alt: 5000,
        Speed: 120,
      };
      const enrichment = { found: false };

      const label = getTrafficLabel(traffic, enrichment);
      expect(label).toBe("123456\n5000ft @ 120kt");
    });
  });

  describe("Traffic Data Management", () => {
    describe("addTrafficData", () => {
      test("should add new traffic data", () => {
        const {addTrafficData} = useTrafficStore.getState();

        const trafficData = [
          {
            Icao_addr: "ABC123",
            Tail: "N123AB",
            Lat: 37.7749,
            Lng: -122.4194,
            Alt: 35000,
            Speed: 450,
            Track: 90,
          },
        ];

        addTrafficData(trafficData);

        const state = useTrafficStore.getState();
        expect(state.trafficData).toHaveLength(1);
        expect(state.trafficData[0]).toEqual({
          ...trafficData[0],
          lastUpdate: 1000000,
        });
      });

      test("should update existing traffic data", () => {
        const {addTrafficData} = useTrafficStore.getState();

        const initialData = [
          {
            Icao_addr: "ABC123",
            Tail: "N123AB",
            Lat: 37.7749,
            Lng: -122.4194,
            Alt: 35000,
          },
        ];

        addTrafficData(initialData);

        // Update the same aircraft
        Date.now = vi.fn(() => 2000000);
        const updatedData = [
          {
            Icao_addr: "ABC123",
            Lat: 37.785,
            Lng: -122.42,
            Alt: 36000,
          },
        ];

        addTrafficData(updatedData);

        const state = useTrafficStore.getState();
        expect(state.trafficData).toHaveLength(1);
        expect(state.trafficData[0]).toEqual({
          Icao_addr: "ABC123",
          Tail: "N123AB", // Preserved from initial data
          Lat: 37.785, // Updated
          Lng: -122.42, // Updated
          Alt: 36000, // Updated
          lastUpdate: 2000000,
        });
      });

      test("should handle multiple aircraft", () => {
        const {addTrafficData} = useTrafficStore.getState();

        const aircraft1 = {
          Icao_addr: "ABC123",
          Tail: "N123AB",
          Lat: 37.7749,
          Lng: -122.4194,
        };

        const aircraft2 = {
          Icao_addr: "DEF456",
          Tail: "N456CD",
          Lat: 40.7128,
          Lng: -74.006,
        };

        addTrafficData([
            aircraft1,
            aircraft2,
        ]);

        const state = useTrafficStore.getState();
        expect(state.trafficData).toHaveLength(2);
        expect(state.trafficData.map((t) => t.Icao_addr)).toContain("ABC123");
        expect(state.trafficData.map((t) => t.Icao_addr)).toContain("DEF456");
      });
    });

    describe("removeStaleTrafficData", () => {
      test("should remove stale traffic data", () => {
        const {addTrafficData, removeStaleTrafficData} =
            useTrafficStore.getState();

        // Add traffic at time 1000000
        Date.now = vi.fn(() => 1000000);
        addTrafficData([
          {
            Icao_addr: "ABC123",
            Lat: 37.7749,
            Lng: -122.4194,
          },
        ]);

        // Add more traffic after 5 seconds
        Date.now = vi.fn(() => 1000000 + 5000);
        addTrafficData([
          {
            Icao_addr: "DEF456",
            Lat: 40.7128,
            Lng: -74.006,
          },
        ]);

        // Check for stale traffic 15 seconds later
        // First aircraft should be stale
        // Second aircraft should be fresh
        Date.now = vi.fn(() => 1000000 + 15000);
        removeStaleTrafficData();

        const state = useTrafficStore.getState();
        expect(state.trafficData).toHaveLength(1);
        expect(state.trafficData[0].Icao_addr).toBe("DEF456");
      });

      test("should remove all stale traffic", () => {
        const {addTrafficData, removeStaleTrafficData} =
            useTrafficStore.getState();

        Date.now = vi.fn(() => 1000000);
        const data = [
          {Icao_addr: "ABC123", Lat: 37.7749, Lng: -122.4194},
          {Icao_addr: "DEF456", Lat: 40.7128, Lng: -74.006},
        ]
        addTrafficData(data);

        // 20 seconds later - both should be stale
        Date.now = vi.fn(() => 1000000 + 20000);
        removeStaleTrafficData();

        const state = useTrafficStore.getState();
        expect(state.trafficData).toEqual([]);
      });

      test("should keep fresh traffic data", () => {
        const {addTrafficData, removeStaleTrafficData} =
            useTrafficStore.getState();

        Date.now = vi.fn(() => 1000000);
        addTrafficData([
          {Icao_addr: "ABC123", Lat: 37.7749, Lng: -122.4194},
        ]);

        // 5 seconds later - should still be fresh
        Date.now = vi.fn(() => 1000000 + 5000);
        removeStaleTrafficData();

        const state = useTrafficStore.getState();
        expect(state.trafficData).toHaveLength(1);
        expect(state.trafficData[0].Icao_addr).toBe("ABC123");
      });
    });
  });

  describe("renderTrafficData", () => {
    test("should create markers for new traffic data", () => {
      const {addTrafficData, renderTrafficData} = useTrafficStore.getState();

      const trafficData = [
        {
          Icao_addr: "ABC123",
          Tail: "N123AB",
          Lat: 37.7749,
          Lng: -122.4194,
          Alt: 35000,
          Speed: 450,
          Track: 90,
        },
      ];

      addTrafficData(trafficData);
      renderTrafficData();

      const state = useTrafficStore.getState();
      expect(Object.keys(state.trafficMarkers)).toHaveLength(1);

      const marker = state.trafficMarkers["ABC123"];
      expect(marker.lat).toBe(37.7749);
      expect(marker.lon).toBe(-122.4194);
      expect(marker.bearing).toBe(90);
      expect(marker.label).toBe("N123AB\n35000ft @ 450kt");
    });

    test("should update existing markers when traffic data changes", () => {
      const {addTrafficData, renderTrafficData} = useTrafficStore.getState();

      // Add initial traffic
      addTrafficData([
        {
          Icao_addr: "ABC123",
          Tail: "N123AB",
          Lat: 37.7749,
          Lng: -122.4194,
          Alt: 35000,
          Speed: 450,
          Track: 90,
        },
      ]);
      renderTrafficData();

      // Update traffic position
      addTrafficData([
        {
          Icao_addr: "ABC123",
          Lat: 37.785,
          Lng: -122.42,
          Alt: 36000,
          Speed: 460,
          Track: 95,
        },
      ]);
      renderTrafficData();

      const state = useTrafficStore.getState();
      expect(Object.keys(state.trafficMarkers)).toHaveLength(1);

      const marker = state.trafficMarkers["ABC123"];
      expect(marker.lat).toBe(37.785);
      expect(marker.lon).toBe(-122.42);
      expect(marker.bearing).toBe(95);
      expect(marker.label).toBe("N123AB\n36000ft @ 460kt");
    });

    test("should remove markers for aircraft no longer in traffic data", () => {
      const {addTrafficData, renderTrafficData} = useTrafficStore.getState();

      // Manually add a marker that's not in traffic data
      useTrafficStore.setState({
        trafficMarkers: {
          "ABC123": {
            lat: 37.7749,
            lon: -122.4194,
            bearing: 90,
            label: "N123AB\n35000ft @ 450kt",
          },
        },
      });

      // Add legitimate traffic data
      addTrafficData([
        {
          Icao_addr: "ABC123",
          Tail: "N123AB",
          Lat: 37.7749,
          Lng: -122.4194,
        },
      ]);

      renderTrafficData();

      const state = useTrafficStore.getState();
      expect(Object.keys(state.trafficMarkers)).toEqual(["ABC123"]);
      expect(state.trafficMarkers["ORPHAN123"]).toBeUndefined();
    });

    test("should handle traffic with missing optional fields", () => {
      const {addTrafficData, renderTrafficData} = useTrafficStore.getState();

      const trafficData = [
        {
          Icao_addr: "ABC123",
          Lat: 37.7749,
          Lng: -122.4194,
          // Missing Tail, Alt, Speed, Track
        },
      ];

      addTrafficData(trafficData);
      renderTrafficData();

      const state = useTrafficStore.getState();
      const marker = state.trafficMarkers["ABC123"];

      expect(marker.lat).toBe(37.7749);
      expect(marker.lon).toBe(-122.4194);
      expect(marker.bearing).toBeUndefined();
      expect(marker.label).toBe("ABC123\nN/Aft @ N/Akt");
    });
  });

  describe("High-level Operations", () => {
    describe("updateTraffic", () => {
      test("should add traffic data and render markers", () => {
        const {updateTraffic} = useTrafficStore.getState();

        const data = {
          messages: [
            {
              Icao_addr: "ABC123",
              Tail: "N123AB",
              Lat: 37.7749,
              Lng: -122.4194,
              Alt: 35000,
              Speed: 450,
              Track: 90,
            },
          ],
        };
        updateTraffic(data);

        const state = useTrafficStore.getState();
        expect(state.trafficData).toHaveLength(1);
        expect(Object.keys(state.trafficMarkers)).toEqual(["ABC123"]);

        const marker = state.trafficMarkers["ABC123"];
        expect(marker.lat).toBe(37.7749);
        expect(marker.label).toBe("N123AB\n35000ft @ 450kt");
      });
    });

    describe("removeStaleTraffic", () => {
      test("should remove stale data and corresponding markers", () => {
        const {
          renderTrafficData,
          removeStaleTraffic,
        } = useTrafficStore.getState();

        useTrafficStore.setState({
          trafficData: [
            {
              Icao_addr: "OLD123",
              Lat: 37.7749,
              Lng: -122.4194,
              lastUpdate: 1000000,
            },
            {
              Icao_addr: "NEW456",
              Lat: 40.7128,
              Lng: -74.006,
              lastUpdate: 1000000 + 5000,
            },
          ],
        });

        renderTrafficData();

        // Both should have markers
        let state = useTrafficStore.getState();
        expect(Object.keys(state.trafficMarkers)).toHaveLength(2);

        // Remove stale traffic
        Date.now = vi.fn(() => 1000000 + 15000); // 15 seconds later
        removeStaleTraffic();

        state = useTrafficStore.getState();
        expect(state.trafficData).toHaveLength(1);
        expect(state.trafficData[0].Icao_addr).toBe("NEW456");
        expect(Object.keys(state.trafficMarkers)).toEqual(["NEW456"]);
      });
    });
  });
});
