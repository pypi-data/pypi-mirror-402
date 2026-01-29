import { render, screen } from "@testing-library/react";
import StepIntro from "./StepIntro";

describe("StepIntro", () => {
  it("renders title and description", () => {
    render(<StepIntro title="Test Title" description="Test Description" />);

    expect(screen.getByText("Test Title")).toBeInTheDocument();
    expect(screen.getByText("Test Description")).toBeInTheDocument();
  });

  it("applies correct heading styling", () => {
    render(<StepIntro title="My Title" description="My Description" />);

    const heading = screen.getByText("My Title");
    expect(heading.tagName).toBe("H2");
    expect(heading).toHaveClass("font-bold", "text-3xl");
  });

  it("applies correct description styling", () => {
    render(<StepIntro title="Title" description="Description text" />);

    const description = screen.getByText("Description text");
    expect(description.tagName).toBe("P");
  });
});
