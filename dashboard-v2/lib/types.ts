export type DashboardPhase = "boot" | "idle" | "thinking" | "speaking" | "execution";

export type ConnectionStatus = "connecting" | "connected" | "disconnected";

export type CommandDeliveryState = "idle" | "sending" | "accepted" | "failed";

export interface DashboardState {
  phase: DashboardPhase | string;
  status: string;
  muted: boolean;
  connected: boolean;
  qualityTier: "safe" | "high" | "ultra";
}

export interface TelemetrySnapshot {
  cpuPercent: number;
  memoryPercent: number;
  networkInKbps: number;
  networkOutKbps: number;
  diskPercent: number;
}

export interface LogEntry {
  message: string;
  level: "info" | "warning" | "error" | "success" | "debug";
  timestamp: number;
}

export interface ApprovalRequest {
  id: string;
  message: string;
}

export interface RuntimeStatusRecord {
  configReady?: boolean;
  setupRequired?: boolean;
  configError?: string;
  runtimeReady?: boolean;
  runtimeBooting?: boolean;
  current_goal?: string;
  current_step?: string;
  pending_approval?: boolean;
  voice_state?: string;
  total_steps?: number;
  completed_steps?: number;
  elapsed_ms?: number;
  [key: string]: unknown;
}

export interface DashboardSnapshot {
  state: DashboardState;
  logs: LogEntry[];
  runtimeStatus: RuntimeStatusRecord;
  telemetry: TelemetrySnapshot;
  voiceActivity: { level: number };
  approvalRequest: ApprovalRequest | null;
}

export interface DashboardEvent {
  type: string;
  payload: any;
}

export interface CommandSendResult {
  ok: boolean;
  reason?: "empty" | "disconnected";
}

export const DEFAULT_TELEMETRY: TelemetrySnapshot = {
  cpuPercent: 0,
  memoryPercent: 0,
  networkInKbps: 0,
  networkOutKbps: 0,
  diskPercent: 0,
};

export const DEFAULT_SNAPSHOT: DashboardSnapshot = {
  state: {
    phase: "boot",
    status: "BOOTING",
    muted: false,
    connected: false,
    qualityTier: "high",
  },
  logs: [],
  runtimeStatus: {
    configReady: false,
    setupRequired: false,
    configError: "",
    runtimeReady: false,
    runtimeBooting: false,
  },
  telemetry: DEFAULT_TELEMETRY,
  voiceActivity: { level: 0 },
  approvalRequest: null,
};
