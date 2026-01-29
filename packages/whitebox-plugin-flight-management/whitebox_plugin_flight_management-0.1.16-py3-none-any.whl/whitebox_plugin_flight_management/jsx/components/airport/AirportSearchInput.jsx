import { useEffect, useState } from "react";

const { api } = Whitebox;

const AirportSearchInput = ({ placeholder, value, onChange, leftIcon }) => {
  const [inputValue, setInputValue] = useState(value?.name || "");
  const [results, setResults] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);
  const [debounceTimer, setDebounceTimer] = useState(null);

  // Sync inputValue when value.name changes
  useEffect(() => {
    setInputValue(value?.name || "");
  }, [value?.name]);

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
    onChange({
      name: airport.name,
      icao: airport.icao,
      coordinates: airport.coordinates,
    });
  };

  const handleBlur = () => {
    // Delay to allow click on dropdown items
    setTimeout(() => {
      setShowDropdown(false);
    }, 200);
  };

  return (
    <div className="relative flex-1">
      <div className="flex flex-row border border-gray-4 rounded-full px-6 py-4 items-center">
        {leftIcon && <div className="mr-4">{leftIcon}</div>}
        <input
          type="text"
          placeholder={placeholder}
          value={inputValue}
          onChange={handleInputChange}
          onFocus={() => results.length > 0 && setShowDropdown(true)}
          onBlur={handleBlur}
          className="flex-1 outline-none font-light"
        />
      </div>

      {showDropdown && (results.length > 0 || isLoading) && (
        <div className="absolute z-50 w-full mt-2 bg-white border border-gray-4 rounded-2xl shadow-lg max-h-64 overflow-y-auto">
          {isLoading ? (
            <div className="px-4 py-3 text-gray-2 text-sm">Searching...</div>
          ) : (
            results.map((airport, index) => (
              <div
                key={index}
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
  );
};

export default AirportSearchInput;
