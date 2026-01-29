import { render, screen } from "@testing-library/react";
import FlightPlanStep from "./FlightPlanStep";

describe("FlightPlanStep", () => {
  it("renders step intro with correct title and description", () => {
    render(<FlightPlanStep />);

    expect(screen.getByText("Flight Plan")).toBeInTheDocument();
    expect(
      screen.getByText("Add some details to plan out your flight.")
    ).toBeInTheDocument();
  });

  it("renders flight plan inputs", () => {
    render(<FlightPlanStep />);

    expect(
      screen.getByPlaceholderText("Take off Location")
    ).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Arrival Location")).toBeInTheDocument();
    expect(screen.getByText("Add Waypoint")).toBeInTheDocument();
  });
});
