"use client";
import { motion } from "framer-motion";

const cornerPath = "M2,14 L2,2 L14,2";

function Corner({ className }: { className: string }) {
  return (
    <div className={`hud-corner ${className}`}>
      <motion.svg
        width="36"
        height="36"
        viewBox="0 0 16 16"
        fill="none"
        initial={{ opacity: 0, scale: 0.5 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.8, delay: 0.5 }}
      >
        <motion.path
          d={cornerPath}
          stroke="currentColor"
          strokeWidth="1"
          strokeLinecap="round"
          className="text-cyan"
          style={{ opacity: 0.3 }}
          animate={{ opacity: [0.2, 0.5, 0.2] }}
          transition={{ repeat: Infinity, duration: 4, ease: "easeInOut" }}
        />
      </motion.svg>
    </div>
  );
}

export default function HudOverlay() {
  return (
    <>
      <Corner className="hud-tl" />
      <Corner className="hud-tr" />
      <Corner className="hud-bl" />
      <Corner className="hud-br" />
    </>
  );
}
