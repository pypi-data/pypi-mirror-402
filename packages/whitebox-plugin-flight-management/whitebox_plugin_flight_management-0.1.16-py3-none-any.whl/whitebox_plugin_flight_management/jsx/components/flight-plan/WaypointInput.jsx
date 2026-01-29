import { useEffect, useState } from "react";
import useFlightPlanStore from "../../stores/flight_plan";

const { api, importWhiteboxComponent } = Whitebox;

const WaypointInput = ({
  waypoint,
  index,
  onDelete,
  onDragStart,
  onDragOver,
  onDrop,
  onDragEnd,
  isDragging,
  isOver,
}) => {
  const LocationOnIcon = importWhiteboxComponent("icons.location-on");
  const Trash2Icon = importWhiteboxComponent("icons.trash-2");
  const DragIndicatorIcon = importWhiteboxComponent("icons.drag-indicator");
  const TertiaryButton = importWhiteboxComponent("ui.button-tertiary");

  const [inputValue, setInputValue] = useState(waypoint.name || "");
  const [results, setResults] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);
  const [debounceTimer, setDebounceTimer] = useState(null);

  // Sync inputValue when waypoint.name changes (e.g., from reordering)
  useEffect(() => {
    setInputValue(waypoint.name || "");
  }, [waypoint.name]);

  // Cleanup debounce timer on unmount
  useEffect(() => {
    return () => {
      if (debounceTimer) {
        clearTimeout(debounceTimer);
      }
    };
  }, [debounceTimer]);

  const searchAirports = async (query) => {
    if (query.length < 2) {
      setResults([]);
      return;
    }

    setIsLoading(true);
    try {
      const url = api.getPluginProvidedPath("flight.airport-search");
      const response = await api.client.get(url, {
        params: { q: query, limit: 10 },
      });
      setResults(response.data);
      setShowDropdown(true);
    } catch (error) {
      console.error("Failed to search airports:", error);
      setResults([]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleInputChange = (e) => {
    const newValue = e.target.value;
    setInputValue(newValue);

    // Clear previous timer
    if (debounceTimer) {
      clearTimeout(debounceTimer);
    }

    // Set new timer for debounced search
    const timer = setTimeout(() => {
      searchAirports(newValue);
    }, 300);
    setDebounceTimer(timer);
  };

  const handleSelectAirport = (airport) => {
    setInputValue(airport.name);
    setShowDropdown(false);
    setResults([]);

    // Update the waypoint in the store
    const { updateWaypoint } = useFlightPlanStore.getState();
    updateWaypoint(waypoint.id, "name", airport.name);
    updateWaypoint(waypoint.id, "icao", airport.icao);
    updateWaypoint(waypoint.id, "coordinates", airport.coordinates);
  };

  const handleBlur = () => {
    // Delay to allow click on dropdown items
    setTimeout(() => {
      setShowDropdown(false);
    }, 200);
  };

  return (
    <div
      className={`relative flex flex-row w-full items-center gap-4 mb-4 transition-all ${
        isDragging ? "opacity-40" : "opacity-100"
      } ${isOver ? "transform translate-y-2" : ""}`}
      onDragOver={onDragOver}
      onDrop={(e) => onDrop(e, index)}
      onDragEnter={(e) => e.preventDefault()}
    >
      <div className="relative flex-1">
        <div
          className={`flex flex-row border rounded-full px-6 py-4 items-center gap-4 ${
            isOver ? "border-gray-1 border-2" : "border-gray-4"
          }`}
        >
          <LocationOnIcon />
          <input
            type="text"
            placeholder="Waypoint"
            value={inputValue}
            onChange={handleInputChange}
            onFocus={() => results.length > 0 && setShowDropdown(true)}
            onBlur={handleBlur}
            className="flex-1 outline-none font-light"
          />
          <button onClick={() => onDelete(waypoint.id)}>
            <Trash2Icon />
          </button>
        </div>

        {showDropdown && (results.length > 0 || isLoading) && (
          <div className="absolute z-50 w-full mt-2 bg-white border border-gray-4 rounded-2xl shadow-lg max-h-64 overflow-y-auto">
            {isLoading ? (
              <div className="px-4 py-3 text-gray-2 text-sm">Searching...</div>
            ) : (
              results.map((airport, idx) => (
                <div
                  key={idx}
                  className="px-4 py-3 hover:bg-gray-6 cursor-pointer border-b border-gray-5 last:border-b-0"
                  onClick={() => handleSelectAirport(airport)}
                >
                  <div className="font-medium text-gray-1">{airport.name}</div>
                  {airport.icao && (
                    <div className="text-sm text-gray-2">
                      ICAO: {airport.icao}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        )}
      </div>

      <div
        className="absolute -right-10 cursor-grab hover:cursor-grabbing active:cursor-grabbing"
        draggable
        onDragStart={(e) => onDragStart(e, index)}
        onDragEnd={onDragEnd}
      >
        <TertiaryButton leftIcon={<DragIndicatorIcon />} />
      </div>
    </div>
  );
};

export default WaypointInput;
