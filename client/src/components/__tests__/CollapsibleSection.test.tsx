import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import CollapsibleSection from "../CollapsibleSection";

describe("CollapsibleSection", () => {
  it("renders the title", () => {
    render(
      <CollapsibleSection title="Test Title">
        <div>Content</div>
      </CollapsibleSection>
    );
    expect(screen.getByText("Test Title")).toBeInTheDocument();
  });

  it("does not show children when closed (default)", () => {
    render(
      <CollapsibleSection title="Section">
        <div>Hidden Content</div>
      </CollapsibleSection>
    );
    expect(screen.queryByText("Hidden Content")).not.toBeInTheDocument();
  });

  it("shows children when defaultOpen is true", () => {
    render(
      <CollapsibleSection title="Section" defaultOpen={true}>
        <div>Visible Content</div>
      </CollapsibleSection>
    );
    expect(screen.getByText("Visible Content")).toBeInTheDocument();
  });

  it("toggles content visibility on click", () => {
    render(
      <CollapsibleSection title="Section">
        <div>Toggle Content</div>
      </CollapsibleSection>
    );

    // Initially closed
    expect(screen.queryByText("Toggle Content")).not.toBeInTheDocument();

    // Click to open
    fireEvent.click(screen.getByText("Section"));
    expect(screen.getByText("Toggle Content")).toBeInTheDocument();

    // Click to close
    fireEvent.click(screen.getByText("Section"));
    expect(screen.queryByText("Toggle Content")).not.toBeInTheDocument();
  });

  it("shows summary when closed and hides it when open", () => {
    render(
      <CollapsibleSection title="Section" summary={<span>Summary Info</span>}>
        <div>Content</div>
      </CollapsibleSection>
    );

    // Summary visible when closed
    expect(screen.getByText("Summary Info")).toBeInTheDocument();

    // Click to open - summary should hide
    fireEvent.click(screen.getByText("Section"));
    expect(screen.queryByText("Summary Info")).not.toBeInTheDocument();

    // Content now visible
    expect(screen.getByText("Content")).toBeInTheDocument();
  });

  it("renders guide text when open and guide is provided", () => {
    render(
      <CollapsibleSection title="Section" defaultOpen={true} guide="Read me first">
        <div>Content</div>
      </CollapsibleSection>
    );
    expect(screen.getByText("Read me first")).toBeInTheDocument();
  });

  it("renders icon and badge when provided", () => {
    render(
      <CollapsibleSection
        title="Section"
        icon={<span data-testid="icon">I</span>}
        badge={<span data-testid="badge">3</span>}
      >
        <div>Content</div>
      </CollapsibleSection>
    );
    expect(screen.getByTestId("icon")).toBeInTheDocument();
    expect(screen.getByTestId("badge")).toBeInTheDocument();
  });
});
