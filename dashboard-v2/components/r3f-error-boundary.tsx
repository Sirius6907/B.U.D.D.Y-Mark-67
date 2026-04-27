"use client";
import React, { Component, type ReactNode } from "react";

interface Props { children: ReactNode; }
interface State { hasError: boolean; }

export class R3FErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false };

  static getDerivedStateFromError(): State {
    return { hasError: true };
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="absolute inset-0 z-0">
          <div className="absolute inset-0 bg-gradient-to-br from-[#03090f] via-[#050e16] to-[#03090f]" />
          <div className="absolute inset-0 opacity-30"
            style={{
              background:
                "radial-gradient(ellipse at 50% 50%, rgba(92,246,255,0.08), transparent 70%)",
            }}
          />
        </div>
      );
    }
    return this.props.children;
  }
}
