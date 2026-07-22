"use client";

import { useEffect, useState } from "react";

import { fetchHealth } from "@/lib/apiClient";
import { getApiBaseUrl } from "@/lib/env";

import { ErrorState } from "./state/ErrorState";
import { Loading } from "./state/Loading";

type ProbeState = "loading" | "success" | "error";

export function HealthProbe() {
  const [probeState, setProbeState] = useState<ProbeState>("loading");
  const [healthStatus, setHealthStatus] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    fetchHealth(getApiBaseUrl())
      .then((health) => {
        if (cancelled) {
          return;
        }

        setHealthStatus(health.status);
        setProbeState("success");
      })
      .catch(() => {
        if (!cancelled) {
          setProbeState("error");
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  if (probeState === "loading") {
    return <Loading message="Checking API health..." />;
  }

  if (probeState === "error") {
    return <ErrorState message="Could not reach the backend API." />;
  }

  return (
    <p role="status" aria-live="polite">
      Backend health: {healthStatus}
    </p>
  );
}
