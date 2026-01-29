import AirportSearchInput from "../airport/AirportSearchInput";

const LocationInput = ({ leftIcon, placeholder, value, onChange }) => {
  return (
    <div className="flex flex-row mb-4 items-center">
      <AirportSearchInput
        leftIcon={leftIcon}
        placeholder={placeholder}
        value={value}
        onChange={onChange}
      />
    </div>
  );
};

export default LocationInput;
