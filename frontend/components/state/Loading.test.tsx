import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { Loading } from "./Loading";

describe("Loading", () => {
  it("announces the loading state to assistive technologies", () => {
    render(<Loading message="Loading data..." />);

    expect(screen.getByRole("status")).toHaveTextContent("Loading data...");
  });
});
