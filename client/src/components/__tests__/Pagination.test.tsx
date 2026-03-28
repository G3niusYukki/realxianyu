import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import Pagination from "../Pagination";

describe("Pagination", () => {
  it("returns null when total pages <= 1 (total equals pageSize)", () => {
    const { container } = render(
      <Pagination current={1} total={10} pageSize={10} onChange={() => {}} />
    );
    expect(container.innerHTML).toBe("");
  });

  it("returns null when total is 0", () => {
    const { container } = render(
      <Pagination current={1} total={0} pageSize={10} onChange={() => {}} />
    );
    expect(container.innerHTML).toBe("");
  });

  it("renders pagination when total pages > 1", () => {
    render(
      <Pagination current={1} total={30} pageSize={10} onChange={() => {}} />
    );
    expect(screen.getByLabelText("第 1 页")).toBeInTheDocument();
    expect(screen.getByLabelText("第 2 页")).toBeInTheDocument();
    expect(screen.getByLabelText("第 3 页")).toBeInTheDocument();
  });

  it("calls onChange when a page button is clicked", () => {
    const onChange = vi.fn();
    render(
      <Pagination current={1} total={30} pageSize={10} onChange={onChange} />
    );

    fireEvent.click(screen.getByLabelText("第 2 页"));
    expect(onChange).toHaveBeenCalledWith(2);
  });

  it("calls onChange when next button is clicked", () => {
    const onChange = vi.fn();
    render(
      <Pagination current={1} total={30} pageSize={10} onChange={onChange} />
    );

    fireEvent.click(screen.getByLabelText("下一页"));
    expect(onChange).toHaveBeenCalledWith(2);
  });

  it("calls onChange when previous button is clicked", () => {
    const onChange = vi.fn();
    render(
      <Pagination current={2} total={30} pageSize={10} onChange={onChange} />
    );

    fireEvent.click(screen.getByLabelText("上一页"));
    expect(onChange).toHaveBeenCalledWith(1);
  });

  it("disables previous button on first page", () => {
    render(
      <Pagination current={1} total={30} pageSize={10} onChange={() => {}} />
    );
    expect(screen.getByLabelText("上一页")).toBeDisabled();
  });

  it("disables next button on last page", () => {
    render(
      <Pagination current={3} total={30} pageSize={10} onChange={() => {}} />
    );
    expect(screen.getByLabelText("下一页")).toBeDisabled();
  });

  it("marks current page with aria-current", () => {
    render(
      <Pagination current={2} total={30} pageSize={10} onChange={() => {}} />
    );
    expect(screen.getByLabelText("第 2 页")).toHaveAttribute(
      "aria-current",
      "page"
    );
    expect(screen.getByLabelText("第 1 页")).not.toHaveAttribute(
      "aria-current"
    );
  });

  it("shows total count", () => {
    render(
      <Pagination current={1} total={42} pageSize={10} onChange={() => {}} />
    );
    expect(screen.getByText("42")).toBeInTheDocument();
  });
});
