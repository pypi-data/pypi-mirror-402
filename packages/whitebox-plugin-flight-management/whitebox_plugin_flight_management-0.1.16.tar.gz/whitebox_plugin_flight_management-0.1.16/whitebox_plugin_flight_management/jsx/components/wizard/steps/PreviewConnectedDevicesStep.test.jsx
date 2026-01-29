import { render, screen } from "@testing-library/react";
import PreviewConnectedDevicesStep from "./PreviewConnectedDevicesStep";

describe("PreviewConnectedDevicesStep", () => {
  it("renders step intro with correct title and description", () => {
    render(<PreviewConnectedDevicesStep />);

    expect(screen.getByText("Preview Connected Devices")).toBeInTheDocument();
    expect(
      screen.getByText(
        "Preview the inputs to ensure everything is in place and connected."
      )
    ).toBeInTheDocument();
  });
});
