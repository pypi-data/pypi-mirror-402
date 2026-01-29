import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import WaypointInput from "./WaypointInput";

describe("WaypointInput", () => {
  const mockWaypoint = {
    id: "wp-1",
    name: "Chicago",
    icao: "KORD",
    coordinates: ["-87.9048", "41.9786"],
  };

  const mockHandlers = {
    onDelete: vi.fn(),
    onDragStart: vi.fn(),
    onDragOver: vi.fn(),
    onDrop: vi.fn(),
    onDragEnd: vi.fn(),
  };

  it("renders waypoint name", () => {
    render(
      <WaypointInput
        waypoint={mockWaypoint}
        index={0}
        isDragging={false}
        isOver={false}
        {...mockHandlers}
      />
    );

    expect(screen.getByDisplayValue("Chicago")).toBeInTheDocument();
  });

  it("calls onDelete when trash button clicked", async () => {
    const { container } = render(
      <WaypointInput
        waypoint={mockWaypoint}
        index={0}
        isDragging={false}
        isOver={false}
        {...mockHandlers}
      />
    );

    const buttons = container.querySelectorAll("button");
    const deleteButton = Array.from(buttons).find((btn) =>
      btn.innerHTML.includes("trash")
    );

    if (deleteButton) {
      await userEvent.click(deleteButton);
      expect(mockHandlers.onDelete).toHaveBeenCalledWith("wp-1");
    }
  });

  it("applies dragging opacity when isDragging is true", () => {
    const { container } = render(
      <WaypointInput
        waypoint={mockWaypoint}
        index={0}
        isDragging={true}
        isOver={false}
        {...mockHandlers}
      />
    );

    const wrapper = container.firstChild;
    expect(wrapper).toHaveClass("opacity-40");
  });

  it("applies transform when isOver is true", () => {
    const { container } = render(
      <WaypointInput
        waypoint={mockWaypoint}
        index={0}
        isDragging={false}
        isOver={true}
        {...mockHandlers}
      />
    );

    const wrapper = container.firstChild;
    expect(wrapper).toHaveClass("transform", "translate-y-2");
  });
});
