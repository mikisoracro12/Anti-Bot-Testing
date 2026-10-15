import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { StatusBadge } from "./StatusBadge";

describe("StatusBadge", () => {
  it("renders allowed status", () => {
    render(<StatusBadge value="allowed" />);
    expect(screen.getByText("allowed")).toBeInTheDocument();
  });

  it("renders placeholder for empty value", () => {
    render(<StatusBadge value={null} />);
    expect(screen.getByText("—")).toBeInTheDocument();
  });
});
