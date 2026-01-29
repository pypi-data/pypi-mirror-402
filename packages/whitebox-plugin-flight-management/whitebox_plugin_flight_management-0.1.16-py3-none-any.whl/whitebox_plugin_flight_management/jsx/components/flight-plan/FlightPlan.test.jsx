import { render, screen } from "@testing-library/react";
import FlightPlan from "./FlightPlan";

describe("FlightPlan", () => {
  it("renders takeoff and arrival inputs", () => {
    render(<FlightPlan />);

    expect(
      screen.getByPlaceholderText("Take off Location")
    ).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Arrival Location")).toBeInTheDocument();
  });

  it("renders add waypoint button", () => {
    render(<FlightPlan />);

    expect(screen.getByText("Add Waypoint")).toBeInTheDocument();
  });
});
