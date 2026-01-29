import useFlightPlanStore from "./flight_plan";

describe("useFlightPlanStore", () => {
  const getState = useFlightPlanStore.getState;

  beforeEach(() => {
    // Reset store to initial state before each test
    getState().resetFlightPlan();
  });

  describe("initial state", () => {
    it("has empty locations and waypoints", () => {
      const state = getState();
      expect(state.takeOffLocation).toEqual({
        name: "",
        icao: "",
        coordinates: ["", ""],
      });
      expect(state.arrivalLocation).toEqual({
        name: "",
        icao: "",
        coordinates: ["", ""],
      });
      expect(state.waypoints).toEqual([]);
    });
  });

  describe("location setters", () => {
    it("setTakeOffLocation sets takeoff location", () => {
      const location = {
        name: "Red Wheelbarrow BBQ",
        icao: "RWBBQ",
        coordinates: ["40.7434791", "-73.9889899"],
      };
      getState().setTakeOffLocation(location);
      expect(getState().takeOffLocation).toEqual(location);
    });

    it("setArrivalLocation sets arrival location", () => {
      const location = {
        name: "Red Wheelbarrow BBQ",
        icao: "RWBBQ",
        coordinates: ["40.7434791", "-73.9889899"],
      };
      getState().setArrivalLocation(location);
      expect(getState().arrivalLocation).toEqual(location);
    });

    it("setWaypoints sets all waypoints", () => {
      const waypoints = [
        { id: "1", name: "WP1", icao: "WP1", coordinates: ["1", "2"] },
        { id: "2", name: "WP2", icao: "WP2", coordinates: ["3", "4"] },
      ];
      getState().setWaypoints(waypoints);
      expect(getState().waypoints).toEqual(waypoints);
    });
  });

  describe("location updaters", () => {
    it("updateTakeOffLocation updates specific field", () => {
      getState().updateTakeOffLocation("name", "JFK");
      expect(getState().takeOffLocation.name).toBe("JFK");
      expect(getState().takeOffLocation.icao).toBe("");

      getState().updateTakeOffLocation("icao", "KJFK");
      expect(getState().takeOffLocation.icao).toBe("KJFK");
    });

    it("updateArrivalLocation updates specific field", () => {
      getState().updateArrivalLocation("name", "LAX");
      expect(getState().arrivalLocation.name).toBe("LAX");
      expect(getState().arrivalLocation.icao).toBe("");

      getState().updateArrivalLocation("coordinates", ["-118.4085", "33.9416"]);
      expect(getState().arrivalLocation.coordinates).toEqual([
        "-118.4085",
        "33.9416",
      ]);
    });
  });

  describe("waypoint management", () => {
    it("addWaypoint adds a new waypoint with generated id", () => {
      expect(getState().waypoints).toHaveLength(0);

      getState().addWaypoint();
      expect(getState().waypoints).toHaveLength(1);
      expect(getState().waypoints[0]).toMatchObject({
        name: "",
        icao: "",
        coordinates: ["", ""],
      });
      expect(getState().waypoints[0].id).toMatch(/^waypoint-\d+$/);

      getState().addWaypoint();
      expect(getState().waypoints).toHaveLength(2);
    });

    it("updateWaypoint updates specific waypoint field", () => {
      getState().addWaypoint();
      const waypointId = getState().waypoints[0].id;

      getState().updateWaypoint(waypointId, "name", "Waypoint 1");
      expect(getState().waypoints[0].name).toBe("Waypoint 1");

      getState().updateWaypoint(waypointId, "icao", "WP1");
      expect(getState().waypoints[0].icao).toBe("WP1");

      getState().updateWaypoint(waypointId, "coordinates", ["1.5", "2.5"]);
      expect(getState().waypoints[0].coordinates).toEqual(["1.5", "2.5"]);
    });

    it("updateWaypoint only updates matching waypoint", () => {
      const waypoints = [
        { id: "wp-1", name: "", icao: "", coordinates: ["", ""] },
        { id: "wp-2", name: "", icao: "", coordinates: ["", ""] },
      ];
      getState().setWaypoints(waypoints);

      getState().updateWaypoint("wp-1", "name", "First");
      expect(getState().waypoints[0].name).toBe("First");
      expect(getState().waypoints[1].name).toBe("");
    });

    it("deleteWaypoint removes waypoint by id", () => {
      const waypoints = [
        { id: "wp-1", name: "First", icao: "", coordinates: ["", ""] },
        { id: "wp-2", name: "Second", icao: "", coordinates: ["", ""] },
        { id: "wp-3", name: "Third", icao: "", coordinates: ["", ""] },
      ];
      getState().setWaypoints(waypoints);
      expect(getState().waypoints).toHaveLength(3);

      getState().deleteWaypoint("wp-2");
      expect(getState().waypoints).toHaveLength(2);
      expect(getState().waypoints.find((w) => w.id === "wp-2")).toBeUndefined();
      expect(getState().waypoints[0].name).toBe("First");
      expect(getState().waypoints[1].name).toBe("Third");
    });

    it("reorderWaypoints moves waypoint from start to end index", () => {
      const waypoints = [
        { id: "1", name: "First", icao: "", coordinates: ["", ""] },
        { id: "2", name: "Second", icao: "", coordinates: ["", ""] },
        { id: "3", name: "Third", icao: "", coordinates: ["", ""] },
      ];
      getState().setWaypoints(waypoints);

      // Move first to last position
      getState().reorderWaypoints(0, 2);
      const result = getState().waypoints;
      expect(result[0].name).toBe("Second");
      expect(result[1].name).toBe("Third");
      expect(result[2].name).toBe("First");
    });

    it("reorderWaypoints moves waypoint from end to start index", () => {
      const waypoints = [
        { id: "1", name: "First", icao: "", coordinates: ["", ""] },
        { id: "2", name: "Second", icao: "", coordinates: ["", ""] },
        { id: "3", name: "Third", icao: "", coordinates: ["", ""] },
      ];
      getState().setWaypoints(waypoints);

      // Move last to first position
      getState().reorderWaypoints(2, 0);
      const result = getState().waypoints;
      expect(result[0].name).toBe("Third");
      expect(result[1].name).toBe("First");
      expect(result[2].name).toBe("Second");
    });
  });

  describe("getFlightPlan", () => {
    it("returns all flight plan data", () => {
      const takeoff = { name: "JFK", icao: "KJFK", coordinates: ["1", "2"] };
      const arrival = { name: "LAX", icao: "KLAX", coordinates: ["3", "4"] };
      const waypoints = [
        { id: "1", name: "WP1", icao: "WP1", coordinates: ["5", "6"] },
      ];

      getState().setTakeOffLocation(takeoff);
      getState().setArrivalLocation(arrival);
      getState().setWaypoints(waypoints);

      const flightPlan = getState().getFlightPlan();
      expect(flightPlan).toEqual({
        takeOffLocation: takeoff,
        waypoints: waypoints,
        arrivalLocation: arrival,
      });
    });
  });

  describe("resetFlightPlan", () => {
    it("resets all data to initial state", () => {
      // Set some data
      getState().setTakeOffLocation({
        name: "JFK",
        icao: "KJFK",
        coordinates: ["1", "2"],
      });
      getState().setArrivalLocation({
        name: "LAX",
        icao: "KLAX",
        coordinates: ["3", "4"],
      });
      getState().addWaypoint();

      expect(getState().takeOffLocation.name).toBe("JFK");
      expect(getState().arrivalLocation.name).toBe("LAX");
      expect(getState().waypoints).toHaveLength(1);

      // Reset
      getState().resetFlightPlan();

      expect(getState().takeOffLocation).toEqual({
        name: "",
        icao: "",
        coordinates: ["", ""],
      });
      expect(getState().arrivalLocation).toEqual({
        name: "",
        icao: "",
        coordinates: ["", ""],
      });
      expect(getState().waypoints).toEqual([]);
    });
  });
});
