import { useEffect, useState } from "react";
import { Polyline, CircleMarker, Tooltip } from "react-leaflet";
import useFlightPlanStore from "./stores/flight_plan";
import useMissionControlStore from "./stores/mission_control";

// Flight plan visualization colors (update as needed for theme)
const COLORS = {
  route: "#E318E0",
  takeoff: "#E318E0",
  arrival: "#E318E0",
  waypoint: "#E318E0",
  marker: "#E7C8E7",
};

const SIZES = {
  lineWeight: 4,
  markerRadius: 10,
  waypointRadius: 8,
  markerBorder: 3,
};

// Converts a location object to a Leaflet-compatible coordinate pair
const locationToLatLng = (location) => {
  if (
    !location ||
    !location.coordinates ||
    !location.coordinates[0] ||
    !location.coordinates[1]
  ) {
    return null;
  }
  const [lng, lat] = location.coordinates;
  return [lat, lng];
};

// Builds the flight plan route from takeoff through waypoints to arrival
const useFlightPlanRoute = () => {
  const { takeOffLocation, arrivalLocation, waypoints } = useFlightPlanStore();
  const [route, setRoute] = useState({ points: [], locations: [] });

  useEffect(() => {
    const points = [];
    const locations = [];

    // Takeoff
    const takeoffCoords = locationToLatLng(takeOffLocation);
    if (takeoffCoords) {
      points.push(takeoffCoords);
      locations.push({
        position: takeoffCoords,
        name: takeOffLocation.name || "Takeoff",
        icao: takeOffLocation.icao,
        type: "takeoff",
      });
    }

    // Waypoints in order
    waypoints.forEach((waypoint, index) => {
      const coords = locationToLatLng(waypoint);
      if (coords) {
        points.push(coords);
        locations.push({
          position: coords,
          name: waypoint.name || `Waypoint ${index + 1}`,
          icao: waypoint.icao,
          type: "waypoint",
          waypointIndex: index + 1,
        });
      }
    });

    // Arrival
    const arrivalCoords = locationToLatLng(arrivalLocation);
    if (arrivalCoords) {
      points.push(arrivalCoords);
      locations.push({
        position: arrivalCoords,
        name: arrivalLocation.name || "Arrival",
        icao: arrivalLocation.icao,
        type: "arrival",
      });
    }

    setRoute({ points, locations });
  }, [takeOffLocation, arrivalLocation, waypoints]);

  return route;
};

// Marker for a single flight plan location (takeoff, waypoint, or arrival)
const FlightPlanLocationMarker = ({ location }) => {
  const getMarkerStyle = () => {
    switch (location.type) {
      case "takeoff":
        return {
          radius: SIZES.markerRadius,
          fillColor: COLORS.takeoff,
          label: "Takeoff",
        };
      case "arrival":
        return {
          radius: SIZES.markerRadius,
          fillColor: COLORS.arrival,
          label: "Arrival",
        };
      case "waypoint":
        return {
          radius: SIZES.waypointRadius,
          fillColor: COLORS.waypoint,
          label: `Waypoint ${location.waypointIndex}`,
        };
      default:
        return {
          radius: SIZES.waypointRadius,
          fillColor: COLORS.waypoint,
          label: "Unknown",
        };
    }
  };

  const style = getMarkerStyle();

  return (
    <CircleMarker
      center={location.position}
      radius={style.radius}
      pathOptions={{
        color: COLORS.marker,
        weight: SIZES.markerBorder,
        fillColor: style.fillColor,
        fillOpacity: 1,
      }}
    >
      <Tooltip direction="top" offset={[0, -10]} opacity={0.9}>
        <div className="text-sm">
          <div className="font-semibold">{location.name}</div>
          {location.icao && (
            <div className="text-xs text-gray-2">ICAO: {location.icao}</div>
          )}
          <div className="text-xs text-gray-3">{style.label}</div>
        </div>
      </Tooltip>
    </CircleMarker>
  );
};

// Main flight plan overlay component
// Renders the flight route line and location markers on the map
const FlightPlanOverlay = () => {
  const { points, locations } = useFlightPlanRoute();
  const mode = useMissionControlStore((state) => state.mode);
  const isFlightActive = useMissionControlStore((state) =>
    state.isFlightSessionActive()
  );

  // Need at least 2 points to draw a route
  if (points.length < 2) {
    return null;
  }

  // Only show overlay during active flight or playback
  const shouldShowOverlay = mode === "playback" || isFlightActive;
  if (!shouldShowOverlay) return null;

  return (
    <>
      {/* Flight route line */}
      <Polyline
        positions={points}
        pathOptions={{
          color: COLORS.route,
          weight: SIZES.lineWeight,
          opacity: 0.8,
        }}
      />

      {/* Location markers */}
      {locations.map((location, index) => (
        <FlightPlanLocationMarker key={index} location={location} />
      ))}
    </>
  );
};

export { FlightPlanOverlay };
export default FlightPlanOverlay;
