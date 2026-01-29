import { render, screen } from "@testing-library/react";
import LocationInput from "./LocationInput";

describe("LocationInput", () => {
  it("renders with placeholder", () => {
    const mockOnChange = vi.fn();

    render(
      <LocationInput
        placeholder="Take off Location"
        value={{ name: "" }}
        onChange={mockOnChange}
      />
    );

    expect(
      screen.getByPlaceholderText("Take off Location")
    ).toBeInTheDocument();
  });

  it("renders with left icon", () => {
    const mockOnChange = vi.fn();
    const leftIcon = <span data-testid="test-icon">Icon</span>;

    render(
      <LocationInput
        leftIcon={leftIcon}
        placeholder="Location"
        value={{ name: "" }}
        onChange={mockOnChange}
      />
    );

    expect(screen.getByTestId("test-icon")).toBeInTheDocument();
  });

  it("displays location name", () => {
    const mockOnChange = vi.fn();

    render(
      <LocationInput
        placeholder="Location"
        value={{ name: "JFK International" }}
        onChange={mockOnChange}
      />
    );

    expect(screen.getByDisplayValue("JFK International")).toBeInTheDocument();
  });
});
