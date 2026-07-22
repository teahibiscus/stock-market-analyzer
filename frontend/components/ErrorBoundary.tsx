"use client";

import { Component, type ErrorInfo, type ReactNode } from "react";

import { ErrorState } from "./state/ErrorState";

type ErrorBoundaryProps = {
  children: ReactNode;
};

type ErrorBoundaryState = {
  hasError: boolean;
};

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = { hasError: false };

  static getDerivedStateFromError(): ErrorBoundaryState {
    return { hasError: true };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("Application error boundary caught an error.", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return <ErrorState message="The application encountered an unexpected error." />;
    }

    return this.props.children;
  }
}
