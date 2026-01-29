import { test } from "@tests/setup";
import { expect } from "@playwright/test";
import { mockWhiteboxSocket, waitForWhiteboxSockets } from "@tests/helpers";

test.describe("Traffic Markers Integration", () => {
  test.beforeEach(async ({ page }) => {
    await mockWhiteboxSocket(page, "flight");
    await page.goto("/dashboard");
    await waitForWhiteboxSockets(page, "flight");

    // Wait for the page to load so that the components that register socket
    // event handlers manage to load
    await page.waitForTimeout(1000);

    // Wait for map to be ready
    const leafletMap = page.locator(".leaflet-container").nth(0);
    await expect(leafletMap).toBeVisible();
  });

  test("should start with no traffic markers", async ({ page }) => {
    const leafletMap = page.locator(".leaflet-container").nth(0);
    const trafficMarkers = leafletMap.locator(".traffic-icon-container");

    // Should have no traffic markers initially
    await expect(trafficMarkers).toHaveCount(0);
  });

  test("should render traffic marker after receiving traffic update", async ({
    page,
  }) => {
    const leafletMap = page.locator(".leaflet-container").nth(0);

    // Send traffic update via WebSocket
    await page.evaluate(() => {
      const message = {
        type: "traffic.update",
        messages: [
          {
            Icao_addr: 8393736,
            Reg: "",
            Tail: "AIC2605",
            Lat: 19.38235,
            Lng: 72.75217,
            Alt: 11275,
            Track: 8,
            Speed: 345,
          }
        ]
      };

      const event = new MessageEvent("message", {
        data: JSON.stringify(message),
      });
      const flightSocket = Whitebox.sockets.getSocket("flight", false);
      flightSocket.dispatchEvent(event);
    });

    // Wait for marker to appear
    const trafficMarkers = leafletMap.locator(".traffic-icon-container");
    await expect(trafficMarkers).toHaveCount(1);

    // Verify marker is visible
    const marker = trafficMarkers.first();
    await expect(marker).toBeVisible();
  });

  test("should display multiple traffic markers", async ({ page }) => {
    const leafletMap = page.locator(".leaflet-container").nth(0);

    // Send multiple traffic updates
    await page.evaluate(() => {
      const messages = [
        {
          type: "traffic.update",
          messages: [
            {
              Icao_addr: 8393736,
              Reg: "",
              Tail: "AIC2605",
              Lat: 19.38235,
              Lng: 72.75217,
              Alt: 11275,
              Track: 8,
              Speed: 345,
            }
          ]
        },
        {
          type: "traffic.update",
          messages: [
            {
              Icao_addr: 8393737,
              Reg: "",
              Tail: "AIC2606",
              Lat: 19.48235,
              Lng: 72.85217,
              Alt: 11500,
              Track: 10,
              Speed: 350,
            }
          ]
        },
      ];

      messages.forEach((message) => {
        const event = new MessageEvent("message", {
          data: JSON.stringify(message),
        });
        const flightSocket = Whitebox.sockets.getSocket("flight", false);
        flightSocket.dispatchEvent(event);
      });
    });

    // Should have 2 traffic markers
    const trafficMarkers = leafletMap.locator(".traffic-icon-container");
    await expect(trafficMarkers).toHaveCount(2);
  });

  test("should update marker position when traffic moves", async ({ page }) => {
    const leafletMap = page.locator(".leaflet-container").nth(0);

    // Send initial traffic update
    await page.evaluate(() => {
      const message = {
        type: "traffic.update",
        messages: [
          {
            Icao_addr: 8393736,
            Reg: "",
            Tail: "AIC2605",
            Lat: 19.38235,
            Lng: 72.75217,
            Alt: 11275,
            Track: 8,
            Speed: 345,
          }
        ]
      };

      const event = new MessageEvent("message", {
        data: JSON.stringify(message),
      });
      const flightSocket = Whitebox.sockets.getSocket("flight", false);
      flightSocket.dispatchEvent(event);
    });

    const trafficMarker = leafletMap.locator(".traffic-icon-container").first();
    await expect(trafficMarker).toBeVisible();

    // Get initial position
    const initialPosition = await trafficMarker.evaluate((el) => {
      const transform = el.style.transform;
      return transform ? transform : null;
    });

    // Send updated traffic position
    await page.evaluate(() => {
      const message = {
        type: "traffic.update",
        messages: [
          {
            Icao_addr: 8393736,
            Reg: "",
            Tail: "AIC2605",
            Lat: 19.48235, // New latitude
            Lng: 72.85217, // New longitude
            Alt: 11275,
            Track: 8,
            Speed: 345,
          }
        ]
      };

      const event = new MessageEvent("message", {
        data: JSON.stringify(message),
      });
      const flightSocket = Whitebox.sockets.getSocket("flight", false);
      flightSocket.dispatchEvent(event);
    });

    // Get updated position
    const updatedPosition = await trafficMarker.evaluate((el) => {
      const transform = el.style.transform;
      return transform ? transform : null;
    });

    // Position should have changed
    expect(updatedPosition).not.toBe(initialPosition);
  });

  test("should update marker bearing/rotation", async ({ page }) => {
    const leafletMap = page.locator(".leaflet-container").nth(0);

    // Send initial traffic update
    await page.evaluate(() => {
      const message = {
        type: "traffic.update",
        messages: [
          {
            Icao_addr: 8393736,
            Reg: "",
            Tail: "AIC2605",
            Lat: 19.38235,
            Lng: 72.75217,
            Alt: 11275,
            Track: 8, // Initial bearing
            Speed: 345,
          }
        ]
      };

      const event = new MessageEvent("message", {
        data: JSON.stringify(message),
      });
      const flightSocket = Whitebox.sockets.getSocket("flight", false);
      flightSocket.dispatchEvent(event);
    });

    const trafficMarker = leafletMap.locator(".traffic-icon-container").first();
    await expect(trafficMarker).toBeVisible();

    // Check initial rotation (90 + 8 = 98 degrees)
    await expect(trafficMarker).toHaveAttribute(
      "style",
      expect.stringContaining("rotate(98deg)")
    );

    // Send updated traffic bearing
    await page.evaluate(() => {
      const message = {
        type: "traffic.update",
        messages: [
          {
            Icao_addr: 8393736,
            Reg: "",
            Tail: "AIC2605",
            Lat: 19.38235,
            Lng: 72.75217,
            Alt: 11275,
            Track: 10, // Updated bearing
            Speed: 345,
          }
        ]
      };

      const event = new MessageEvent("message", {
        data: JSON.stringify(message),
      });
      const flightSocket = Whitebox.sockets.getSocket("flight", false);
      flightSocket.dispatchEvent(event);
    });

    // Check updated rotation (90 + 10 = 100 degrees)
    await expect(trafficMarker).toHaveAttribute(
      "style",
      expect.stringContaining("rotate(100deg)")
    );
  });
});
