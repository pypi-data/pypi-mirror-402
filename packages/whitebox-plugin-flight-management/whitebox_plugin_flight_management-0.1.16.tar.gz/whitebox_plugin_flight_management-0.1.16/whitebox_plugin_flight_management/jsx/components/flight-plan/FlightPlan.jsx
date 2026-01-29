import { useState } from "react";
import useFlightPlanStore from "../../stores/flight_plan";
import LocationInput from "./LocationInput";
import WaypointInput from "./WaypointInput";

const { importWhiteboxComponent } = Whitebox;

const AddWaypointButton = () => {
  const SecondaryButton = importWhiteboxComponent("ui.button-secondary");
  const AddIcon = importWhiteboxComponent("icons.add");

  const { addWaypoint } = useFlightPlanStore();

  return (
    <div>
      <SecondaryButton
        text="Add Waypoint"
        leftIcon={<AddIcon />}
        className="w-full font-semibold"
        onClick={addWaypoint}
      />
    </div>
  );
};

const FlightPlan = () => {
  const FlightLandIcon = importWhiteboxComponent("icons.flight-land");
  const FlightTakeoffIcon = importWhiteboxComponent("icons.flight-takeoff");

  const {
    takeOffLocation,
    arrivalLocation,
    waypoints,
    setTakeOffLocation,
    setArrivalLocation,
    deleteWaypoint,
    reorderWaypoints,
  } = useFlightPlanStore();

  const [draggedIndex, setDraggedIndex] = useState(null);
  const [dragOverIndex, setDragOverIndex] = useState(null);

  const handleDragStart = (e, index) => {
    setDraggedIndex(index);
    e.dataTransfer.effectAllowed = "move";
    e.dataTransfer.setData("text/html", e.currentTarget);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = "move";
  };

  const handleDragEnter = (index) => {
    if (draggedIndex !== index) {
      setDragOverIndex(index);
    }
  };

  const handleDragLeave = () => {
    setDragOverIndex(null);
  };

  const handleDrop = (e, dropIndex) => {
    e.preventDefault();
    e.stopPropagation();

    if (draggedIndex !== null && draggedIndex !== dropIndex) {
      reorderWaypoints(draggedIndex, dropIndex);
    }

    setDraggedIndex(null);
    setDragOverIndex(null);
  };

  const handleDragEnd = () => {
    setDraggedIndex(null);
    setDragOverIndex(null);
  };

  return (
    <div>
      <LocationInput
        leftIcon={<FlightTakeoffIcon />}
        placeholder="Take off Location"
        value={takeOffLocation}
        onChange={setTakeOffLocation}
      />
      {waypoints.map((waypoint, index) => (
        <div
          key={waypoint.id}
          onDragEnter={() => handleDragEnter(index)}
          onDragLeave={handleDragLeave}
        >
          <WaypointInput
            waypoint={waypoint}
            index={index}
            onDelete={deleteWaypoint}
            onDragStart={handleDragStart}
            onDragOver={handleDragOver}
            onDrop={handleDrop}
            onDragEnd={handleDragEnd}
            isDragging={draggedIndex === index}
            isOver={dragOverIndex === index && draggedIndex !== index}
          />
        </div>
      ))}
      <LocationInput
        leftIcon={<FlightLandIcon />}
        placeholder="Arrival Location"
        value={arrivalLocation}
        onChange={setArrivalLocation}
      />
      <AddWaypointButton />
    </div>
  );
};

export default FlightPlan;
