"use client";
import { motion, AnimatePresence } from "framer-motion";
import { useRef, useEffect } from "react";
import type { LogEntry } from "@/lib/types";

const LEVEL_COLORS: Record<string, string> = {
  info: "#5cf6ff",
  success: "#8cff66",
  warning: "#ffb800",
  error: "#ff3e3e",
  debug: "#888",
};

const LEVEL_BADGES: Record<string, string> = {
  info: "INF",
  success: "OK ",
  warning: "WRN",
  error: "ERR",
  debug: "DBG",
};

interface Props {
  logs: LogEntry[];
}

export default function LogTerminal({ logs }: Props) {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs.length]);

  return (
    <div className="panel rounded-xl p-4 flex flex-col h-full">
      <div className="flex items-center gap-2 mb-3">
        <div className="w-1.5 h-1.5 rounded-full bg-[#8cff66] animate-pulse-glow" />
        <span className="text-[10px] uppercase tracking-[0.2em] text-muted font-orbitron">System Log</span>
        <span className="ml-auto text-[9px] text-muted opacity-40">{logs.length} entries</span>
      </div>

      <div ref={scrollRef} className="flex-1 overflow-y-auto space-y-0.5 pr-1" style={{ maxHeight: "280px" }}>
        {logs.length === 0 && (
          <div className="flex items-center justify-center h-full">
            <span className="text-[10px] text-muted opacity-40 animate-pulse">Awaiting system output...</span>
          </div>
        )}

        <AnimatePresence initial={false}>
          {logs.slice(-80).map((entry, i) => {
            const color = LEVEL_COLORS[entry.level] || "#888";
            const badge = LEVEL_BADGES[entry.level] || "---";
            const timeText = new Date(entry.timestamp * 1000).toLocaleTimeString("en-US", {
              hour12: false,
              hour: "2-digit",
              minute: "2-digit",
              second: "2-digit",
            });
            return (
              <motion.div
                key={`${entry.timestamp}-${i}`}
                className="flex items-start gap-2 py-0.5 group"
                initial={{ opacity: 0, x: -12 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.25 }}
              >
                <span className="text-[8px] opacity-30 shrink-0 mt-0.5 w-14">{timeText}</span>
                <span className="text-[8px] font-bold tracking-wider shrink-0 mt-0.5 w-7" style={{ color }}>
                  {badge}
                </span>
                <span className="text-[10px] leading-relaxed opacity-75 group-hover:opacity-100 transition-opacity">
                  {entry.message}
                </span>
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>
    </div>
  );
}
