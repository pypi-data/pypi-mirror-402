import { useEffect, useRef, useState } from "react";
import { Marker, Tooltip } from "react-leaflet";
import L from "leaflet";
import useTrafficStore from "./stores/traffic";

const { importWhiteboxStateStore, withStateStore } = Whitebox;

// Our plane icon is tilted by 100deg, so we begin from this offset
const bearingOffset = 100;

const createIcon = (iconUrl, bearing = 0) => {
  return L.divIcon({
    html: `<div style="transform: rotate(${bearingOffset + bearing}deg);">
               <img src="${iconUrl}" style="width: 32px; height: 32px;" />
             </div>`,
    className: "traffic-icon-container",
    iconSize: [32, 32],
    iconAnchor: [16, 16],
  });
};

const TrafficMarker = ({ id, marker }) => {
  const markerRef = useRef(null);
  const [icon, setIcon] = useState(
    marker.iconUrl ? createIcon(marker.iconUrl, marker.bearing) : null
  );

  // Update position without re-rendering
  useEffect(() => {
    if (markerRef.current) {
      markerRef.current.setLatLng([marker.lat, marker.lon]);
    }
  }, [marker.lat, marker.lon]);

  // Update icon when bearing changes
  useEffect(() => {
    if (marker.iconUrl && marker.bearing !== undefined) {
      setIcon(createIcon(marker.iconUrl, marker.bearing));
    }
  }, [marker.bearing, marker.iconUrl]);

  return (
    <Marker position={[marker.lat, marker.lon]} icon={icon} ref={markerRef}>
      {marker.label && (
        <Tooltip direction="bottom" offset={[0, 20]} opacity={1} permanent>
          {marker.label.split("\n").map((line, i) => (
            <div key={i}>{line}</div>
          ))}
        </Tooltip>
      )}
    </Marker>
  );
};

const TrafficMarkersToWrap = () => {
  const useMissionControlStore = importWhiteboxStateStore("flight.mission-control");
  const mode = useMissionControlStore((state) => state.mode);
  const trafficMarkers = useTrafficStore((state) => state.trafficMarkers);

  // Only display traffic markers when in flight mode
  if (mode !== "flight")
    return null;

  return Object.entries(trafficMarkers)
      .filter(([, marker]) => marker.lat && marker.lon)
      .map(([id, marker]) => (
          <TrafficMarker key={id} id={id} marker={marker} />
      ));
};

const TrafficMarkers = withStateStore(
    TrafficMarkersToWrap,
    ["flight.mission-control"],
)

export { TrafficMarkers };
export default TrafficMarkers;
