"use client";

import { motion } from "framer-motion";
import { useEffect } from "react";

interface Props {
  farewell: string;
  onComplete: () => void;
}

const SHUTDOWN_DURATION_MS = 1450;

export default function ShutdownSequence({ farewell, onComplete }: Props) {
  useEffect(() => {
    const timer = window.setTimeout(onComplete, SHUTDOWN_DURATION_MS);
    return () => window.clearTimeout(timer);
  }, [onComplete]);

  return (
    <motion.div
      className="fixed inset-0 z-[120] overflow-hidden"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.28 }}
      style={{ background: "rgba(1,4,8,0.5)" }}
    >
      <div className="absolute inset-0 cinematic-vignette" />
      <motion.div
        className="absolute inset-0 backdrop-blur-sm"
        animate={{ backdropFilter: ["blur(0px)", "blur(8px)", "blur(16px)"] }}
        transition={{ duration: SHUTDOWN_DURATION_MS / 1000, ease: "easeInOut" }}
      />

      <div className="absolute inset-0 flex items-center justify-center">
        <motion.div
          className="relative flex h-[30rem] w-[30rem] items-center justify-center"
          animate={{ scale: [1, 0.92, 0.58, 0.16], opacity: [0.92, 1, 0.7, 0] }}
          transition={{ duration: SHUTDOWN_DURATION_MS / 1000, ease: [0.65, 0, 0.35, 1] }}
        >
          <motion.div
            className="absolute rounded-full border border-fuchsia-400/35"
            style={{ width: 320, height: 320 }}
            animate={{ scale: [1, 0.94, 0.66, 0.24], rotate: [0, 45, -25, 8], opacity: [0.4, 0.7, 0.36, 0] }}
            transition={{ duration: SHUTDOWN_DURATION_MS / 1000, ease: "easeInOut" }}
          />
          <motion.div
            className="absolute rounded-full border border-cyan/20 border-dashed"
            style={{ width: 430, height: 430 }}
            animate={{ scale: [1, 0.88, 0.55, 0.18], rotate: [0, -120, 60, 0], opacity: [0.24, 0.44, 0.15, 0] }}
            transition={{ duration: SHUTDOWN_DURATION_MS / 1000, ease: "easeInOut" }}
          />
          <motion.div
            className="absolute h-40 w-40 rounded-full"
            style={{
              background:
                "radial-gradient(circle, rgba(255,79,216,0.94) 0%, rgba(255,79,216,0.34) 34%, rgba(92,246,255,0.12) 62%, rgba(0,0,0,0) 76%)",
            }}
            animate={{ scale: [1, 0.84, 0.34, 0.04], opacity: [0.85, 1, 0.7, 0] }}
            transition={{ duration: SHUTDOWN_DURATION_MS / 1000, ease: [0.8, 0, 0.2, 1] }}
          />
          <motion.div
            className="absolute h-[2px] w-52 bg-fuchsia-400/70"
            animate={{ scaleX: [1, 0.72, 0.16, 0], opacity: [0.6, 1, 0.7, 0] }}
            transition={{ duration: SHUTDOWN_DURATION_MS / 1000, ease: "easeInOut" }}
          />
        </motion.div>
      </div>

      <div className="absolute inset-x-0 bottom-24 flex justify-center px-6">
        <motion.div
          className="max-w-2xl rounded-2xl border border-fuchsia-400/30 bg-slate-950/50 px-6 py-4 text-center shadow-[0_0_60px_rgba(255,79,216,0.12)] backdrop-blur-md"
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45 }}
        >
          <div className="mb-2 font-orbitron text-[10px] tracking-[0.34em] text-fuchsia-300/85">
            CORE COLLAPSE // POWERING DOWN
          </div>
          <div className="font-mono text-sm leading-7 text-cyan/90">{farewell}</div>
        </motion.div>
      </div>

      <motion.div
        className="absolute inset-0 bg-black"
        initial={{ opacity: 0 }}
        animate={{ opacity: [0, 0.05, 0.18, 0.52, 0.94] }}
        transition={{ duration: SHUTDOWN_DURATION_MS / 1000, ease: "easeInOut" }}
      />
    </motion.div>
  );
}
