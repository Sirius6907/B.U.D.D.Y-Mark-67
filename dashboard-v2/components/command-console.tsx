"use client";
import { useState, type FormEvent } from "react";
import { motion } from "framer-motion";
import type { CommandDeliveryState } from "@/lib/types";

interface Props {
  onSend: (text: string) => { ok: boolean; reason?: string };
  disabled?: boolean;
  deliveryState: CommandDeliveryState;
  muted?: boolean;
}

export default function CommandConsole({ onSend, disabled = false, deliveryState, muted = false }: Props) {
  const [text, setText] = useState("");
  const [focused, setFocused] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    const trimmed = text.trim();
    if (!trimmed) return;
    const result = onSend(trimmed);
    if (result.ok) {
      setText("");
      setErrorMessage("");
      return;
    }
    setErrorMessage(
      result.reason === "disconnected"
        ? "Dashboard link is offline. Command was not sent."
        : "Command cannot be sent yet.",
    );
  };

  return (
    <motion.form
      onSubmit={handleSubmit}
      className="relative z-20"
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.4 }}
    >
      <div
        className="panel rounded-xl p-3 transition-all duration-300"
        style={{
          borderColor: focused ? "var(--border-glow)" : "var(--border)",
          boxShadow: focused
            ? "0 0 24px rgba(92,246,255,0.12), 0 0 0 1px rgba(92,246,255,0.1)"
            : undefined,
        }}
      >
        <div className="flex items-center gap-2 mb-2">
          <span className="text-[10px] uppercase tracking-[0.2em] text-muted font-orbitron">
            Command Interface
          </span>
          <span className="text-cyan animate-blink text-xs">▌</span>
        </div>
        <div className="flex gap-2">
          <input
            type="text"
            value={text}
            onChange={(e) => setText(e.target.value)}
            onFocus={() => setFocused(true)}
            onBlur={() => setFocused(false)}
            disabled={disabled}
            placeholder="Enter command or speak to B.U.D.D.Y..."
            className="flex-1 bg-transparent border-none outline-none text-[11px] text-[var(--text)] placeholder:text-[var(--muted)] placeholder:opacity-30 disabled:opacity-40"
          />
          <motion.button
            type="submit"
            disabled={disabled}
            className="px-4 py-1.5 rounded-lg text-[10px] font-orbitron tracking-wider uppercase disabled:opacity-40"
            style={{
              background: "linear-gradient(135deg, rgba(92,246,255,0.15), rgba(92,246,255,0.05))",
              border: "1px solid var(--border)",
              color: "var(--cyan)",
            }}
            whileHover={{
              borderColor: "var(--border-glow)",
              boxShadow: "0 0 16px rgba(92,246,255,0.2)",
            }}
            whileTap={{ scale: 0.96 }}
          >
            Execute
          </motion.button>
        </div>
        <div className="mt-2 min-h-[14px] text-[9px] font-orbitron tracking-[0.12em] uppercase">
          {muted ? (
            <span className="text-fuchsia-300/80">Microphone muted via F4. Text commands remain active.</span>
          ) : disabled ? (
            <span className="text-amber-300/70">Runtime not ready</span>
          ) : deliveryState === "accepted" ? (
            <span className="text-lime-300/80">Command accepted</span>
          ) : deliveryState === "failed" ? (
            <span className="text-red-300/80">{errorMessage || "Command failed"}</span>
          ) : (
            <span className="text-muted opacity-40">Command channel armed</span>
          )}
        </div>
      </div>
    </motion.form>
  );
}
