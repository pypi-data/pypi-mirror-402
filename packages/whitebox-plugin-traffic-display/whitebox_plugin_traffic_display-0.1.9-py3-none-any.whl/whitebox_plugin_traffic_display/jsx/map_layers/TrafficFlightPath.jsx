import { Polyline } from "react-leaflet";
import useTrafficStore from "../stores/traffic";

const { importWhiteboxStateStore, withStateStore } = Whitebox;

const TrafficFlightPathToWrap = () => {
  const useMissionControlStore = importWhiteboxStateStore("flight.mission-control");
  const flightSession = useMissionControlStore((state) => state.getFlightSession());
  const mode = useMissionControlStore((state) => state.mode);
  const positionData = useTrafficStore((state) => state.positionData);

  // Only display tracks when in-flight
  if (mode !== "flight" || !flightSession || flightSession.ended_at)
    return null;

  const flightSessionStartedAt = new Date(flightSession.started_at).getTime();

  if (positionData.length === 0)
    return null;

  return Object.entries(positionData).map(([entity, data]) => {
    const preparedData = data
        .filter((entry) => entry.timestamp >= flightSessionStartedAt)
        .map((entry) => [entry.latitude, entry.longitude]);

    if (preparedData.length === 0)
      return null;

    return <Polyline key={entity}
                     positions={preparedData}
                     pathOptions={{ color: "blue" }} />;
  });
}

const TrafficFlightPath = withStateStore(
  TrafficFlightPathToWrap,
  ["flight.mission-control"],
)

export { TrafficFlightPath };
export default TrafficFlightPath;
