import type { DashboardSnapshot, DashboardEvent, RuntimeStatusRecord, CommandSendResult } from "./types";

export function reduceDashboardSnapshot(snapshot: DashboardSnapshot, event: DashboardEvent): DashboardSnapshot {
  switch (event.type) {
    case "ui.snapshot":
      return event.payload as DashboardSnapshot;
    case "ui.state.changed":
      return { ...snapshot, state: event.payload };
    case "ui.log.append":
      return { ...snapshot, logs: [...snapshot.logs.slice(-99), event.payload] };
    case "ui.runtime.status":
      return {
        ...snapshot,
        runtimeStatus: {
          ...snapshot.runtimeStatus,
          ...(event.payload as RuntimeStatusRecord),
        },
      };
    case "ui.voice.level":
      return { ...snapshot, voiceActivity: event.payload };
    case "ui.telemetry.snapshot":
      return { ...snapshot, telemetry: event.payload };
    case "ui.approval.requested":
      return { ...snapshot, approvalRequest: event.payload };
    case "ui.approval.cleared":
      return { ...snapshot, approvalRequest: null };
    default:
      return snapshot;
  }
}

export function sendCommandFrame(
  socket: Pick<WebSocket, "readyState" | "send"> | null,
  command: string,
): CommandSendResult {
  const trimmed = command.trim();
  if (!trimmed) {
    return { ok: false, reason: "empty" };
  }
  if (!socket || socket.readyState !== WebSocket.OPEN) {
    return { ok: false, reason: "disconnected" };
  }
  socket.send(
    JSON.stringify({
      type: "ui.command.submitted",
      payload: { command: trimmed },
    }),
  );
  return { ok: true };
}
