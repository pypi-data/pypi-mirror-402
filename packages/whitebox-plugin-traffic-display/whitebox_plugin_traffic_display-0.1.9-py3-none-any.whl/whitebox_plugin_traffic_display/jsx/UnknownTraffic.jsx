import { useEffect, useMemo, useState } from "react";
import useTrafficStore, { getAircraftType } from "./stores/traffic";

const { importWhiteboxComponent } = Whitebox;

const ScrollableOverlay = importWhiteboxComponent("ui.scrollable-overlay");
const AirPlane = importWhiteboxComponent("icons.airplane");

const UnknownFlightCard = ({ trafficId, marker }) => {
  const getAircraftFromCache = useTrafficStore(
    (state) => state.getAircraftFromCache
  );
  const enrichment = getAircraftFromCache(parseInt(trafficId));

  const aircraft = enrichment?.aircraft;

  const displayName =
    aircraft?.registration || marker.label?.split("\n")[0] || "Unknown";
  const aircraftType = getAircraftType(enrichment) || null;
  const operator = aircraft?.operator || null;

  return (
    <div className="flex flex-col gap-2 border border-gray-4 items-start justify-center p-4 rounded-3xl">
      <h1 className="text-gray-1 font-bold">{displayName}</h1>
      {aircraftType && <p className="text-gray-2 text-sm">{aircraftType}</p>}
      {operator && <p className="text-gray-3 text-sm">{operator}</p>}
    </div>
  );
};

const UnknownTraffic = () => {
  const trafficMarkers = useTrafficStore((state) => state.trafficMarkers);
  const [unknownTraffic, setUnknownTraffic] = useState([]);

  const filteredUnknownTraffic = useMemo(() => {
    return Object.entries(trafficMarkers).filter(([, marker]) => {
      return (
        (marker.lat === undefined && marker.lon === undefined) ||
        (marker.lat === 0 && marker.lon === 0)
      );
    });
  }, [trafficMarkers]);

  useEffect(() => {
    setUnknownTraffic(filteredUnknownTraffic);
  }, [filteredUnknownTraffic]);

  return (
    <ScrollableOverlay
      openOverlayIcon={<AirPlane />}
      overlayTitle="Unknown Traffic"
    >
      <div className="overflow-y-auto p-4 space-y-4 flex-1">
        {unknownTraffic.map(([trafficId, marker]) => (
          <UnknownFlightCard key={trafficId} trafficId={trafficId} marker={marker} />
        ))}
      </div>
    </ScrollableOverlay>
  );
};

export default UnknownTraffic;
export { UnknownTraffic };
