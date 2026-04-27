"use client";
import { useEffect, useRef, useState, useCallback } from "react";
import type {
  DashboardSnapshot,
  ConnectionStatus,
  CommandDeliveryState,
} from "./types";
import { DEFAULT_SNAPSHOT } from "./types";
import { reduceDashboardSnapshot, sendCommandFrame } from "./dashboard-protocol";

const RECONNECT_BASE_MS = 1000;
const RECONNECT_MAX_MS = 8000;

declare global {
  interface Window {
    buddyDesktop?: {
      getWebSocketUrl?: () => Promise<string>;
      closeWindow?: () => void;
    };
  }
}

export function useDashboardSocket() {
  const [snapshot, setSnapshot] = useState<DashboardSnapshot>(DEFAULT_SNAPSHOT);
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>("connecting");
  const [commandState, setCommandState] = useState<CommandDeliveryState>("idle");
  const [shutdownFarewell, setShutdownFarewell] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const retryRef = useRef(0);
  const connectionAttemptRef = useRef(0);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const commandResetTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const connect = useCallback(async () => {
    if (wsRef.current && (wsRef.current.readyState === WebSocket.OPEN || wsRef.current.readyState === WebSocket.CONNECTING)) {
      return;
    }
    reconnectTimerRef.current && clearTimeout(reconnectTimerRef.current);
    const attemptId = ++connectionAttemptRef.current;
    setConnectionStatus("connecting");

    const wsUrl =
      (await window.buddyDesktop?.getWebSocketUrl?.()) ??
      process.env.NEXT_PUBLIC_BUDDY_DASHBOARD_WS_URL ??
      "ws://127.0.0.1:8765";

    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      if (attemptId !== connectionAttemptRef.current || wsRef.current !== ws) {
        ws.close();
        return;
      }
      retryRef.current = 0;
      setConnectionStatus("connected");
    };

    ws.onmessage = (ev) => {
      if (attemptId !== connectionAttemptRef.current || wsRef.current !== ws) return;
      try {
        const msg = JSON.parse(ev.data);
        if (msg?.type === "ui.shutdown.requested") {
          setShutdownFarewell(String(msg?.payload?.farewell || ""));
        }
        setSnapshot((prev) => reduceDashboardSnapshot(prev, msg));
      } catch {
        // Ignore malformed frames.
      }
    };

    ws.onclose = () => {
      if (wsRef.current === ws) {
        wsRef.current = null;
      }
      if (attemptId !== connectionAttemptRef.current) return;
      setConnectionStatus("disconnected");
      const delay = Math.min(RECONNECT_BASE_MS * 2 ** retryRef.current, RECONNECT_MAX_MS);
      retryRef.current += 1;
      reconnectTimerRef.current = setTimeout(() => {
        void connect();
      }, delay);
    };

    ws.onerror = () => {
      if (attemptId === connectionAttemptRef.current) {
        ws.close();
      }
    };
  }, []);

  useEffect(() => {
    void connect();
    return () => {
      connectionAttemptRef.current += 1;
      reconnectTimerRef.current && clearTimeout(reconnectTimerRef.current);
      commandResetTimerRef.current && clearTimeout(commandResetTimerRef.current);
      wsRef.current?.close();
    };
  }, [connect]);

  const sendCommand = useCallback((text: string) => {
    setCommandState("sending");
    const result = sendCommandFrame(wsRef.current, text);
    if (!result.ok) {
      setCommandState("failed");
      return result;
    }
    setCommandState("accepted");
    commandResetTimerRef.current && clearTimeout(commandResetTimerRef.current);
    commandResetTimerRef.current = setTimeout(() => setCommandState("idle"), 1200);
    return result;
  }, []);

  const sendApproval = useCallback((id: string, approved: boolean) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({
          type: "ui.approval.resolved",
          payload: { id, approved },
        }),
      );
    }
  }, []);

  const submitConfig = useCallback((payload: Record<string, string>) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({
          type: "ui.config.submit",
          payload,
        }),
      );
      return true;
    }
    return false;
  }, []);

  const notifyBootComplete = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: "ui.boot.completed", payload: {} }));
      return true;
    }
    return false;
  }, []);

  const closeWindow = useCallback(() => {
    window.buddyDesktop?.closeWindow?.();
  }, []);

  return {
    snapshot,
    connectionStatus,
    commandState,
    shutdownFarewell,
    sendCommand,
    sendApproval,
    submitConfig,
    notifyBootComplete,
    closeWindow,
  };
}
