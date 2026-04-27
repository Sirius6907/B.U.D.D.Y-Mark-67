"use client";
import { motion, AnimatePresence } from "framer-motion";
import type { ApprovalRequest } from "@/lib/types";

interface Props {
  request: ApprovalRequest;
  onRespond: (id: string, approved: boolean) => void;
}

export default function ApprovalModal({ request, onRespond }: Props) {
  return (
    <AnimatePresence>
      <motion.div
        className="fixed inset-0 z-50 flex items-center justify-center"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
      >
        <motion.div className="absolute inset-0 bg-black/60 backdrop-blur-sm" initial={{ opacity: 0 }} animate={{ opacity: 1 }} />

        <motion.div
          className="relative panel-glow rounded-2xl p-6 max-w-md w-full mx-4"
          style={{
            background: "linear-gradient(180deg, rgba(15,30,45,0.95), rgba(8,18,28,0.98))",
            border: "1px solid rgba(255,180,0,0.35)",
            boxShadow: "0 0 40px rgba(255,180,0,0.1), 0 30px 80px rgba(0,0,0,0.6)",
          }}
          initial={{ opacity: 0, scale: 0.85, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.9, y: 10 }}
          transition={{ type: "spring", damping: 20, stiffness: 300 }}
        >
          <div className="flex items-center gap-2 mb-4">
            <motion.div
              className="w-2 h-2 rounded-full bg-[#ffb800]"
              animate={{
                boxShadow: [
                  "0 0 4px rgba(255,180,0,0.4)",
                  "0 0 16px rgba(255,180,0,0.8)",
                  "0 0 4px rgba(255,180,0,0.4)",
                ],
              }}
              transition={{ repeat: Infinity, duration: 1.5 }}
            />
            <span className="font-orbitron text-[11px] tracking-[0.2em] text-amber uppercase">Authorization Required</span>
          </div>

          <div className="mb-6">
            <h3 className="text-sm font-semibold mb-2 text-[var(--text)]">Runtime approval requested</h3>
            <p className="text-[11px] leading-relaxed text-muted">{request.message}</p>
          </div>

          <div className="flex gap-3">
            <motion.button
              onClick={() => onRespond(request.id, true)}
              className="flex-1 py-2.5 rounded-lg font-orbitron text-[10px] tracking-wider uppercase"
              style={{
                background: "linear-gradient(135deg, rgba(140,255,102,0.15), rgba(140,255,102,0.05))",
                border: "1px solid rgba(140,255,102,0.3)",
                color: "#8cff66",
              }}
              whileHover={{ borderColor: "rgba(140,255,102,0.6)", boxShadow: "0 0 20px rgba(140,255,102,0.15)" }}
              whileTap={{ scale: 0.96 }}
            >
              Authorize
            </motion.button>
            <motion.button
              onClick={() => onRespond(request.id, false)}
              className="flex-1 py-2.5 rounded-lg font-orbitron text-[10px] tracking-wider uppercase"
              style={{
                background: "linear-gradient(135deg, rgba(255,62,62,0.15), rgba(255,62,62,0.05))",
                border: "1px solid rgba(255,62,62,0.3)",
                color: "#ff3e3e",
              }}
              whileHover={{ borderColor: "rgba(255,62,62,0.6)", boxShadow: "0 0 20px rgba(255,62,62,0.15)" }}
              whileTap={{ scale: 0.96 }}
            >
              Deny
            </motion.button>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
