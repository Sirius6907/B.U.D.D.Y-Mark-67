"use client";
import { motion } from "framer-motion";
import { useEffect, useState } from "react";
import type { ConnectionStatus } from "@/lib/types";

const STATUS_CONFIG: Record<ConnectionStatus, { color: string; label: string }> = {
  connected: { color: "#8cff66", label: "ONLINE" },
  connecting: { color: "#ffb800", label: "LINKING" },
  disconnected: { color: "#ff3e3e", label: "OFFLINE" },
};

interface Props {
  connectionStatus: ConnectionStatus;
  phase: string;
  systemStatus: string;
  muted: boolean;
}

export default function TopBar({ connectionStatus, phase, systemStatus, muted }: Props) {
  const status = STATUS_CONFIG[connectionStatus];

  return (
    <motion.header
      className="relative z-30 flex items-center justify-between px-5 py-3"
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, delay: 0.2 }}
    >
      <div className="flex items-center gap-3">
        <div className="w-2 h-2 rounded-full animate-pulse-glow" style={{ background: "#5cf6ff" }} />
        <h1 className="font-orbitron text-sm font-bold tracking-[0.25em] text-cyan">B.U.D.D.Y</h1>
        <span className="text-[9px] font-orbitron tracking-[0.2em] text-muted opacity-60">MARK LXVII</span>
      </div>

      <motion.div
        className="absolute left-1/2 -translate-x-1/2 font-orbitron text-[10px] tracking-[0.3em] uppercase text-muted"
        key={`${phase}-${systemStatus}`}
        initial={{ opacity: 0 }}
        animate={{ opacity: 0.6 }}
        transition={{ duration: 0.4 }}
      >
        {muted ? "MIC: MUTED" : `PHASE: ${phase.toUpperCase()}`}
      </motion.div>

      <div className="flex items-center gap-3">
        {muted ? (
          <div className="rounded-full border border-fuchsia-400/50 bg-fuchsia-500/10 px-2 py-1">
            <span className="text-[9px] font-orbitron tracking-[0.18em] text-fuchsia-300">MUTED</span>
          </div>
        ) : null}
        <div className="flex items-center gap-1.5">
          <motion.div
            className="w-1.5 h-1.5 rounded-full"
            style={{ background: status.color }}
            animate={{
              boxShadow: [
                `0 0 4px ${status.color}60`,
                `0 0 12px ${status.color}80`,
                `0 0 4px ${status.color}60`,
              ],
            }}
            transition={{ repeat: Infinity, duration: 2 }}
          />
          <span className="text-[9px] font-orbitron tracking-[0.15em]" style={{ color: status.color }}>
            {status.label}
          </span>
        </div>
        <Clock />
      </div>
    </motion.header>
  );
}

function Clock() {
  const [time, setTime] = useState("--:--:--");

  useEffect(() => {
    const formatTime = () =>
      new Date().toLocaleTimeString("en-US", {
        hour12: false,
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
      });

    setTime(formatTime());
    const timer = window.setInterval(() => {
      setTime(formatTime());
    }, 1000);

    return () => window.clearInterval(timer);
  }, []);

  return <span className="text-[9px] font-orbitron tracking-wider text-muted opacity-50">{time}</span>;
}
