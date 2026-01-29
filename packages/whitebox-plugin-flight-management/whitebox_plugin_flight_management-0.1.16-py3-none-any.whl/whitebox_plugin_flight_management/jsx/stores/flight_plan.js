import { create } from "zustand";

const flightPlanSlice = (set, get) => ({
  // Each location is an object with: {name: str, icao: str, coordinates: [str, str]}
  takeOffLocation: { name: "", icao: "", coordinates: ["", ""] },
  arrivalLocation: { name: "", icao: "", coordinates: ["", ""] },
  waypoints: [],

  // Set take off location
  setTakeOffLocation: (location) => set({ takeOffLocation: location }),

  // Set arrival location
  setArrivalLocation: (location) => set({ arrivalLocation: location }),

  // Set all waypoints
  setWaypoints: (waypoints) => set({ waypoints }),

  // Update a specific field in takeoff location
  updateTakeOffLocation: (field, value) => {
    set((state) => ({
      takeOffLocation: { ...state.takeOffLocation, [field]: value },
    }));
  },

  // Update a specific field in arrival location
  updateArrivalLocation: (field, value) => {
    set((state) => ({
      arrivalLocation: { ...state.arrivalLocation, [field]: value },
    }));
  },

  // Add a new waypoint
  addWaypoint: () => {
    const newWaypoint = {
      id: `waypoint-${Date.now()}`,
      name: "",
      icao: "",
      coordinates: ["", ""],
    };
    set((state) => ({
      waypoints: [...state.waypoints, newWaypoint],
    }));
  },

  // Update waypoint field
  updateWaypoint: (id, field, value) => {
    set((state) => ({
      waypoints: state.waypoints.map((waypoint) =>
        waypoint.id === id ? { ...waypoint, [field]: value } : waypoint
      ),
    }));
  },

  // Delete a waypoint
  deleteWaypoint: (id) => {
    set((state) => ({
      waypoints: state.waypoints.filter((waypoint) => waypoint.id !== id),
    }));
  },

  // Reorder waypoints
  reorderWaypoints: (startIndex, endIndex) => {
    set((state) => {
      const result = Array.from(state.waypoints);
      const [removed] = result.splice(startIndex, 1);
      result.splice(endIndex, 0, removed);
      return { waypoints: result };
    });
  },

  // Get all flight plan data
  getFlightPlan: () => {
    const { takeOffLocation, arrivalLocation, waypoints } = get();
    return {
      takeOffLocation,
      waypoints,
      arrivalLocation,
    };
  },

  // Reset flight plan
  resetFlightPlan: () =>
    set({
      takeOffLocation: { name: "", icao: "", coordinates: ["", ""] },
      arrivalLocation: { name: "", icao: "", coordinates: ["", ""] },
      waypoints: [],
    }),
});

const useFlightPlanStore = create(flightPlanSlice);

export default useFlightPlanStore;
