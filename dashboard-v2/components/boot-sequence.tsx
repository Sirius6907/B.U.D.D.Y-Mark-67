"use client";

import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useMemo, useState } from "react";
import type { ConnectionStatus } from "@/lib/types";

const BOOT_MIN_DURATION_MS = 7000;

const BOOT_LINES = [
  "REACTOR CHAMBER PRESSURIZED",
  "SINGULARITY CORE WAKE SIGNAL CONFIRMED",
  "GLYPH LATTICE SPINNING INTO PHASE",
  "MEMORY CONSTELLATION MOUNTED",
  "VOICE FABRIC COHERENCE REACHED",
  "NEURAL UPLINK LOCKED TO LOCAL HOST",
  "BATTLESPACE TELEMETRY GRID SYNCHRONIZED",
  "B.U.D.D.Y COMMAND INTELLIGENCE NOW STABLE",
];

interface Props {
  connectionStatus: ConnectionStatus;
  onBootComplete: () => void;
}

export default function BootSequence({ connectionStatus, onBootComplete }: Props) {
  const [elapsedMs, setElapsedMs] = useState(0);
  const [lineCount, setLineCount] = useState(0);

  useEffect(() => {
    const start = performance.now();
    const ticker = window.setInterval(() => {
      setElapsedMs(performance.now() - start);
    }, 50);
    return () => window.clearInterval(ticker);
  }, []);

  useEffect(() => {
    const stepMs = BOOT_MIN_DURATION_MS / (BOOT_LINES.length + 1);
    const nextCount = Math.min(BOOT_LINES.length, Math.floor(elapsedMs / stepMs));
    if (nextCount !== lineCount) {
      setLineCount(nextCount);
    }
  }, [elapsedMs, lineCount]);

  useEffect(() => {
    if (elapsedMs >= BOOT_MIN_DURATION_MS && connectionStatus === "connected") {
      const timer = window.setTimeout(onBootComplete, 350);
      return () => window.clearTimeout(timer);
    }
  }, [elapsedMs, connectionStatus, onBootComplete]);

  const progress = Math.min(1, elapsedMs / BOOT_MIN_DURATION_MS);
  const visibleLines = useMemo(() => BOOT_LINES.slice(0, lineCount), [lineCount]);

  return (
    <motion.div
      className="fixed inset-0 z-[100] overflow-hidden"
      style={{ background: "radial-gradient(circle at 50% 38%, rgba(121, 40, 202, 0.16), transparent 22%), #010408" }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.8 }}
    >
      <div className="absolute inset-0 cinematic-noise opacity-40" />
      <div className="absolute inset-0 cinematic-vignette" />
      <motion.div
        className="absolute left-1/2 top-1/2 h-[34rem] w-[34rem] -translate-x-1/2 -translate-y-1/2 rounded-full"
        style={{
          background:
            "radial-gradient(circle, rgba(255,79,216,0.18) 0%, rgba(111,0,255,0.12) 24%, rgba(0,0,0,0) 70%)",
        }}
        animate={{ scale: [0.7, 1.06, 0.92, 1], opacity: [0.25, 0.6, 0.45, 0.72] }}
        transition={{ duration: 6.2, times: [0, 0.28, 0.72, 1], ease: "easeInOut" }}
      />

      <motion.div
        className="absolute left-1/2 top-1/2 h-[26rem] w-[26rem] -translate-x-1/2 -translate-y-1/2 rounded-full border"
        style={{ borderColor: "rgba(92,246,255,0.22)" }}
        animate={{ rotate: 360, opacity: [0.12, 0.35, 0.18] }}
        transition={{ rotate: { repeat: Infinity, duration: 24, ease: "linear" }, opacity: { duration: 4, repeat: Infinity } }}
      />
      <motion.div
        className="absolute left-1/2 top-1/2 h-[18rem] w-[18rem] -translate-x-1/2 -translate-y-1/2 rounded-full border border-dashed"
        style={{ borderColor: "rgba(255,79,216,0.3)" }}
        animate={{ rotate: -360, scale: [0.9, 1.02, 0.96, 1] }}
        transition={{
          rotate: { repeat: Infinity, duration: 11, ease: "linear" },
          scale: { duration: 3.6, repeat: Infinity, ease: "easeInOut" },
        }}
      />

      <div className="absolute inset-0 flex flex-col items-center justify-center px-6">
        <motion.div
          className="mb-10 text-center"
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1.1, ease: "easeOut" }}
        >
          <motion.div
            className="mb-4 h-[1px] w-60"
            style={{ background: "linear-gradient(90deg, transparent, rgba(92,246,255,0.8), transparent)" }}
            animate={{ opacity: [0.18, 0.95, 0.18], scaleX: [0.82, 1.06, 0.92] }}
            transition={{ duration: 2.2, repeat: Infinity, ease: "easeInOut" }}
          />
          <h1 className="font-orbitron text-[2.1rem] font-extrabold tracking-[0.55em] text-cyan">
            B.U.D.D.Y
          </h1>
          <p className="mt-2 font-orbitron text-[10px] tracking-[0.48em] text-fuchsia-300/80">
            SINGULARITY COMMAND CORTEX // MARK LXVII
          </p>
        </motion.div>

        <div className="relative mb-10 h-44 w-[34rem] max-w-full overflow-hidden rounded-2xl border border-cyan/20 bg-slate-950/35 px-5 py-4 backdrop-blur-md">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(92,246,255,0.09),transparent_46%)]" />
          <motion.div
            className="absolute inset-y-0 left-0 w-32"
            style={{ background: "linear-gradient(90deg, rgba(92,246,255,0.12), transparent)" }}
            animate={{ x: ["-120%", "320%"] }}
            transition={{ duration: 2.6, repeat: Infinity, ease: "linear" }}
          />
          <div className="relative z-10 flex h-full flex-col justify-between">
            <div className="flex items-center justify-between">
              <span className="font-orbitron text-[10px] tracking-[0.36em] text-cyan/90">ALIEN CORE BOOTSTRAP</span>
              <span className="font-orbitron text-[10px] tracking-[0.24em] text-fuchsia-300/75">
                {Math.round(progress * 100)}%
              </span>
            </div>
            <div className="space-y-2 font-mono text-[11px]">
              <AnimatePresence>
                {visibleLines.map((line) => (
                  <motion.div
                    key={line}
                    className="flex items-center gap-2 text-cyan/75"
                    initial={{ opacity: 0, x: -16, filter: "blur(4px)" }}
                    animate={{ opacity: 1, x: 0, filter: "blur(0px)" }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 0.36 }}
                  >
                    <span className="text-lime/80">▸</span>
                    <span>{line}</span>
                  </motion.div>
                ))}
              </AnimatePresence>
              {lineCount < BOOT_LINES.length ? (
                <motion.div
                  className="flex items-center gap-2 text-fuchsia-300/70"
                  animate={{ opacity: [0.35, 1, 0.35] }}
                  transition={{ repeat: Infinity, duration: 1.2 }}
                >
                  <span>▸</span>
                  <span>WAITING FOR CORE STABILIZATION</span>
                </motion.div>
              ) : null}
            </div>
            <div>
              <div className="mb-2 flex items-center justify-between text-[10px] font-orbitron tracking-[0.24em] text-muted">
                <span>
                  {connectionStatus === "connected"
                    ? "UPLINK SEALED"
                    : connectionStatus === "connecting"
                    ? "NEGOTIATING UPLINK"
                    : "REACQUIRING UPLINK"}
                </span>
                <span>{Math.max(0, ((BOOT_MIN_DURATION_MS - elapsedMs) / 1000)).toFixed(1)}s</span>
              </div>
              <div className="h-1.5 overflow-hidden rounded-full bg-cyan/10">
                <motion.div
                  className="h-full rounded-full"
                  style={{ background: "linear-gradient(90deg, #5cf6ff, #ff4fd8 65%, #8cff66)" }}
                  animate={{ width: `${progress * 100}%` }}
                  transition={{ duration: 0.15, ease: "linear" }}
                />
              </div>
            </div>
          </div>
        </div>

        <motion.div
          className="relative h-24 w-24 rounded-full border border-cyan/25"
          animate={{ scale: [0.86, 1.06, 0.94, 1], opacity: [0.38, 1, 0.72, 0.9] }}
          transition={{ duration: 3.2, repeat: Infinity, ease: "easeInOut" }}
        >
          <motion.div
            className="absolute inset-4 rounded-full"
            style={{ background: "radial-gradient(circle, rgba(255,79,216,0.82), rgba(255,79,216,0.08) 72%, transparent)" }}
            animate={{ scale: [0.82, 1.18, 0.88], rotate: [0, 35, -20, 0] }}
            transition={{ duration: 2.4, repeat: Infinity, ease: "easeInOut" }}
          />
        </motion.div>
      </div>
    </motion.div>
  );
}
