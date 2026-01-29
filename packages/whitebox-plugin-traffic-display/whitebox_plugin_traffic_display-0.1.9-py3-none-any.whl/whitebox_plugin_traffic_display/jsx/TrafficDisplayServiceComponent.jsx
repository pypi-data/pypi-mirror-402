import { useEffect } from "react";
import useTrafficStore from "./stores/traffic";

const TrafficDisplayServiceComponent = () => {
  const updateTraffic = useTrafficStore((state) => state.updateTraffic);
  const removeStaleTraffic = useTrafficStore(
    (state) => state.removeStaleTraffic
  );
  const staleTrafficRemovalInterval = useTrafficStore(
    (state) => state.staleTrafficRemovalInterval
  );

  useEffect(() => {
    // Set up stale traffic removal interval
    const interval = setInterval(() => {
      removeStaleTraffic();
    }, staleTrafficRemovalInterval);

    // Set up WebSocket listener for traffic updates
    const removeListener = Whitebox.sockets.addEventListener(
      "flight",
      "message",
      (event) => {
        const data = JSON.parse(event.data);
        if (data.type === "traffic.update") {
          updateTraffic(data);
        }
      }
    );

    // Cleanup both interval and WebSocket listener
    return () => {
      clearInterval(interval);
      removeListener();
    };
  }, []);

  return null;
}

export { TrafficDisplayServiceComponent };
export default TrafficDisplayServiceComponent;
