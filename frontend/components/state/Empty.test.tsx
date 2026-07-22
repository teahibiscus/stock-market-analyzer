import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { Empty } from "./Empty";

describe("Empty", () => {
  it("renders the empty-state message", () => {
    render(<Empty message="No results found." />);

    expect(screen.getByRole("status")).toHaveTextContent("No results found.");
  });
});
