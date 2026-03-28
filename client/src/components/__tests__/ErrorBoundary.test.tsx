import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi, afterEach } from "vitest";
import ErrorBoundary from "../ErrorBoundary";

// Suppress React error-boundary console noise in tests
afterEach(() => {
  vi.restoreAllMocks();
});

describe("ErrorBoundary", () => {
  it("renders children when no error", () => {
    render(
      <ErrorBoundary>
        <p>Child content</p>
      </ErrorBoundary>
    );
    expect(screen.getByText("Child content")).toBeInTheDocument();
  });

  it("renders fallback UI when a child throws", () => {
    vi.spyOn(console, "error").mockImplementation(() => {});

    const Throwing = () => {
      throw new Error("boom");
    };

    render(
      <ErrorBoundary>
        <Throwing />
      </ErrorBoundary>
    );

    expect(screen.getByText("页面出错了")).toBeInTheDocument();
    expect(
      screen.getByText(/请刷新页面重试/)
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "刷新页面" })
    ).toBeInTheDocument();
  });

  it("does not render children after error", () => {
    vi.spyOn(console, "error").mockImplementation(() => {});

    const Throwing = () => {
      throw new Error("boom");
    };

    render(
      <ErrorBoundary>
        <Throwing />
        <p>Should not appear</p>
      </ErrorBoundary>
    );

    expect(screen.queryByText("Should not appear")).not.toBeInTheDocument();
  });
});
