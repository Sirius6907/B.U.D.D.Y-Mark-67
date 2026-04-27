"use client";
import { motion } from "framer-motion";
import type { TelemetrySnapshot } from "@/lib/types";

interface GaugeProps {
  label: string;
  value: number;
  max?: number;
  unit: string;
  color: string;
  icon: string;
}

function CircularGauge({ label, value, max = 100, unit, color, icon }: GaugeProps) {
  const v = typeof value === "number" && isFinite(value) ? value : 0;
  const pct = Math.min(v / max, 1);
  const radius = 34;
  const circumference = 2 * Math.PI * radius;
  const dashOffset = circumference * (1 - pct);

  return (
    <div className="flex flex-col items-center gap-1.5">
      <div className="relative w-20 h-20">
        <svg className="w-full h-full -rotate-90" viewBox="0 0 80 80">
          <circle cx="40" cy="40" r={radius} fill="none" stroke={`${color}15`} strokeWidth="3" />
          <motion.circle
            cx="40"
            cy="40"
            r={radius}
            fill="none"
            stroke={color}
            strokeWidth="3"
            strokeLinecap="round"
            strokeDasharray={circumference}
            animate={{ strokeDashoffset: dashOffset }}
            transition={{ duration: 0.8, ease: "easeOut" }}
            style={{ filter: `drop-shadow(0 0 6px ${color}80)` }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-[10px] opacity-50">{icon}</span>
          <motion.span
            className="text-sm font-bold font-orbitron"
            style={{ color }}
            key={Math.round(v)}
            initial={{ opacity: 0.6 }}
            animate={{ opacity: 1 }}
          >
            {v < 10 ? v.toFixed(1) : Math.round(v)}
          </motion.span>
          <span className="text-[8px] uppercase tracking-wider opacity-40">{unit}</span>
        </div>
      </div>
      <span className="text-[9px] uppercase tracking-[0.15em] text-muted">{label}</span>
    </div>
  );
}

interface Props {
  telemetry: TelemetrySnapshot;
}

export default function TelemetryPanel({ telemetry }: Props) {
  return (
    <div className="panel rounded-xl p-4">
      <div className="flex items-center gap-2 mb-4">
        <div className="w-1.5 h-1.5 rounded-full bg-[#5cf6ff] animate-pulse-glow" />
        <span className="text-[10px] uppercase tracking-[0.2em] text-muted font-orbitron">System Telemetry</span>
      </div>

      <div className="grid grid-cols-3 gap-3 mb-3">
        <CircularGauge label="CPU" value={telemetry.cpuPercent} unit="%" color="#5cf6ff" icon="⚡" />
        <CircularGauge label="Memory" value={telemetry.memoryPercent} unit="%" color="#ff4fd8" icon="◈" />
        <CircularGauge label="Disk" value={telemetry.diskPercent} unit="%" color="#8cff66" icon="◉" />
      </div>

      <div className="space-y-2 pt-2 border-t border-[var(--border)]">
        <NetworkBar label="NET ↓" value={telemetry.networkInKbps} color="#5cf6ff" />
        <NetworkBar label="NET ↑" value={telemetry.networkOutKbps} color="#ff4fd8" />
      </div>
    </div>
  );
}

function NetworkBar({ label, value = 0, color }: { label: string; value: number; color: string }) {
  const v = value ?? 0;
  const pct = Math.min(v / 500, 1) * 100;
  return (
    <div className="flex items-center gap-2">
      <span className="text-[9px] w-10 text-muted uppercase tracking-wider">{label}</span>
      <div className="flex-1 h-1.5 rounded-full overflow-hidden" style={{ background: `${color}12` }}>
        <motion.div
          className="h-full rounded-full"
          style={{ background: `linear-gradient(90deg, ${color}80, ${color})` }}
          animate={{ width: `${Math.max(2, pct)}%` }}
          transition={{ duration: 0.6 }}
        />
      </div>
      <span className="text-[9px] w-14 text-right font-orbitron" style={{ color }}>
        {v.toFixed(1)} <span className="opacity-50">KB/s</span>
      </span>
    </div>
  );
}
