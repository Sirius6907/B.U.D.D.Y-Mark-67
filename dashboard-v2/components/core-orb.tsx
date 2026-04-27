"use client";
import { motion } from "framer-motion";

const PHASE_COLORS: Record<string, string> = {
  boot: "#5cf6ff",
  idle: "#8cff66",
  thinking: "#ffb800",
  speaking: "#ff4fd8",
  execution: "#ff3e3e",
  muted: "#ff4fd8",
};

const PHASE_LABELS: Record<string, string> = {
  boot: "INITIALIZING",
  idle: "STANDBY",
  thinking: "PROCESSING",
  speaking: "VOCALIZING",
  execution: "EXECUTING",
  muted: "MUTED",
};

interface Props {
  phase: string;
  voiceLevel: number;
  muted?: boolean;
}

export default function CoreOrb({ phase, voiceLevel, muted = false }: Props) {
  const effectivePhase = muted ? "muted" : phase;
  const color = PHASE_COLORS[effectivePhase] || "#5cf6ff";
  const scale = 1 + voiceLevel * 0.25;
  const energy = Math.max(0.18, Math.min(1, 0.28 + voiceLevel));

  return (
    <div className="flex flex-col items-center justify-center gap-4 relative">
      <div
        className="absolute rounded-full blur-3xl"
        style={{
          width: 240,
          height: 240,
          background: `radial-gradient(circle, ${color}18, transparent 70%)`,
        }}
      />
      <motion.div
        className="absolute rounded-full"
        style={{
          width: 290,
          height: 290,
          background: `radial-gradient(circle, ${color}10, transparent 64%)`,
        }}
        animate={{ scale: [0.92, 1.08, 0.96], opacity: [0.25, 0.55, 0.3] }}
        transition={{ duration: 4.2, repeat: Infinity, ease: "easeInOut" }}
      />

      <motion.div
        className="absolute rounded-full border border-dashed"
        style={{ width: 200, height: 200, borderColor: `${color}25` }}
        animate={{ rotate: 360 }}
        transition={{ repeat: Infinity, duration: 30, ease: "linear" }}
      />
      <motion.div
        className="absolute rounded-full border"
        style={{ width: 170, height: 170, borderColor: `${color}30` }}
        animate={{ rotate: -360 }}
        transition={{ repeat: Infinity, duration: 20, ease: "linear" }}
      />
      <motion.div
        className="absolute rounded-full border border-dashed"
        style={{ width: 140, height: 140, borderColor: `${color}45` }}
        animate={{ rotate: 360 }}
        transition={{ repeat: Infinity, duration: 12, ease: "linear" }}
      />

      <motion.div
        className="relative rounded-full flex items-center justify-center"
        style={{
          width: 100,
          height: 100,
          background: `radial-gradient(circle at 35% 35%, ${color}60, ${color}15 60%, transparent 100%)`,
          boxShadow: `0 0 40px ${color}40, 0 0 80px ${color}18, inset 0 0 30px ${color}20`,
        }}
        animate={{ scale: [scale, scale * 1.06, scale] }}
        transition={{ repeat: Infinity, duration: 2, ease: "easeInOut" }}
      >
        <motion.div
          className="absolute rounded-full border"
          style={{
            inset: -14,
            borderColor: `${color}25`,
            boxShadow: `0 0 28px ${color}18`,
          }}
          animate={{ scale: [0.94, 1.06, 0.98], opacity: [0.2, 0.75, 0.3] }}
          transition={{ duration: 2.2, repeat: Infinity, ease: "easeInOut" }}
        />
        <div
          className="rounded-full"
          style={{
            width: 32,
            height: 32,
            background: `radial-gradient(circle, ${color}90, ${color}30)`,
            boxShadow: `0 0 20px ${color}60`,
          }}
        />
      </motion.div>

      <motion.div
        className="font-orbitron text-xs tracking-[0.3em] uppercase"
        style={{ color }}
        key={effectivePhase}
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
      >
        {muted ? "MUTED" : PHASE_LABELS[phase] || phase.toUpperCase()}
      </motion.div>

      <div className="w-28 h-1 rounded-full overflow-hidden" style={{ background: `${color}15` }}>
        <motion.div
          className="h-full rounded-full"
          style={{ background: color }}
          animate={{ width: `${Math.max(5, voiceLevel * 100)}%`, opacity: [energy, 1, energy] }}
          transition={{ duration: 0.1 }}
        />
      </div>
    </div>
  );
}
