import { render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { HealthProbe } from "./HealthProbe";
import * as apiClient from "@/lib/apiClient";

describe("HealthProbe", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("shows loading then success when the backend health check succeeds", async () => {
    vi.spyOn(apiClient, "fetchHealth").mockResolvedValue({ status: "ok" });

    render(<HealthProbe />);

    expect(screen.getByRole("status")).toHaveTextContent("Checking API health...");

    await waitFor(() => {
      expect(screen.getByRole("status")).toHaveTextContent("Backend health: ok");
    });
  });

  it("shows an error state when the backend health check fails", async () => {
    vi.spyOn(apiClient, "fetchHealth").mockRejectedValue(new Error("network error"));

    render(<HealthProbe />);

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent("Could not reach the backend API.");
    });
  });
});
