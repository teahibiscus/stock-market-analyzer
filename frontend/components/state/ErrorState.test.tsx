import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ErrorState } from "./ErrorState";

describe("ErrorState", () => {
  it("renders the error alert with the provided message", () => {
    render(<ErrorState message="Something went wrong." />);

    expect(screen.getByRole("alert")).toHaveTextContent("Something went wrong.");
  });
});
