import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import AirportSearchInput from "./AirportSearchInput";

describe("AirportSearchInput", () => {
  const mockOnChange = vi.fn();

  it("renders with placeholder", () => {
    render(
      <AirportSearchInput
        placeholder="Search airports"
        value={{ name: "" }}
        onChange={mockOnChange}
      />
    );

    const input = screen.getByPlaceholderText("Search airports");
    expect(input).toBeInTheDocument();
  });

  it("displays value name in input", () => {
    render(
      <AirportSearchInput
        placeholder="Search"
        value={{ name: "JFK International" }}
        onChange={mockOnChange}
      />
    );

    const input = screen.getByDisplayValue("JFK International");
    expect(input).toBeInTheDocument();
  });

  it("allows typing in input", async () => {
    render(
      <AirportSearchInput
        placeholder="Search"
        value={{ name: "" }}
        onChange={mockOnChange}
      />
    );

    const input = screen.getByPlaceholderText("Search");
    await userEvent.type(input, "JFK");

    expect(input).toHaveValue("JFK");
  });

  it("renders with left icon", () => {
    const leftIcon = <span data-testid="test-icon">Icon</span>;

    render(
      <AirportSearchInput
        placeholder="Search"
        value={{ name: "" }}
        onChange={mockOnChange}
        leftIcon={leftIcon}
      />
    );

    expect(screen.getByTestId("test-icon")).toBeInTheDocument();
  });
});
