import test from "node:test";
import assert from "node:assert/strict";

import { reduceDashboardSnapshot, sendCommandFrame } from "../lib/dashboard-protocol";
import { DEFAULT_SNAPSHOT } from "../lib/types";

test("reduceDashboardSnapshot applies incremental events", () => {
  let snapshot = DEFAULT_SNAPSHOT;
  snapshot = reduceDashboardSnapshot(snapshot, {
    type: "ui.state.changed",
    payload: { phase: "thinking", status: "THINKING", muted: false, connected: true, qualityTier: "high" },
  });
  snapshot = reduceDashboardSnapshot(snapshot, {
    type: "ui.log.append",
    payload: { message: "SYS: online", level: "info", timestamp: 1 },
  });
  snapshot = reduceDashboardSnapshot(snapshot, {
    type: "ui.telemetry.snapshot",
    payload: { cpuPercent: 10, memoryPercent: 20, networkInKbps: 5, networkOutKbps: 2, diskPercent: 3 },
  });

  assert.equal(snapshot.state.status, "THINKING");
  assert.equal(snapshot.logs[0]?.message, "SYS: online");
  assert.equal(snapshot.telemetry.cpuPercent, 10);
});

test("sendCommandFrame fails when socket is unavailable", () => {
  const result = sendCommandFrame(null, "hello");
  assert.equal(result.ok, false);
  assert.equal(result.reason, "disconnected");
});

test("sendCommandFrame sends payload when socket is open", () => {
  let sent = "";
  const fakeSocket = {
    readyState: 1,
    send(payload: string) {
      sent = payload;
    },
  } as unknown as WebSocket;

  const result = sendCommandFrame(fakeSocket, "hello");
  assert.equal(result.ok, true);
  assert.match(sent, /ui\.command\.submitted/);
  assert.match(sent, /hello/);
});
