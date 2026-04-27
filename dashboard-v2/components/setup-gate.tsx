"use client";
import { FormEvent, useState } from "react";
import { motion } from "framer-motion";

interface Props {
  error?: string;
  onSubmit: (payload: {
    geminiApiKey: string;
    telegramBotToken: string;
    telegramUsername: string;
    telegramUserId: string;
    osSystem: string;
  }) => boolean;
}

export default function SetupGate({ error = "", onSubmit }: Props) {
  const [geminiApiKey, setGeminiApiKey] = useState("");
  const [telegramBotToken, setTelegramBotToken] = useState("");
  const [telegramUsername, setTelegramUsername] = useState("");
  const [telegramUserId, setTelegramUserId] = useState("");
  const [localError, setLocalError] = useState("");

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    if (!geminiApiKey.trim()) {
      setLocalError("Gemini API key is required.");
      return;
    }
    const ok = onSubmit({
      geminiApiKey,
      telegramBotToken,
      telegramUsername,
      telegramUserId,
      osSystem: "windows",
    });
    setLocalError(ok ? "" : "Unable to reach the runtime bridge.");
  };

  return (
    <motion.div
      className="fixed inset-0 z-[120] flex items-center justify-center bg-black/70 backdrop-blur-md"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
    >
      <motion.form
        onSubmit={handleSubmit}
        className="panel-glow w-full max-w-2xl rounded-2xl p-6 mx-4"
        style={{
          background: "linear-gradient(180deg, rgba(12,24,36,0.98), rgba(6,14,22,0.98))",
          border: "1px solid rgba(92,246,255,0.18)",
        }}
        initial={{ opacity: 0, scale: 0.95, y: 10 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
      >
        <div className="mb-4">
          <div className="font-orbitron text-xs uppercase tracking-[0.3em] text-cyan">Initial Configuration</div>
          <h2 className="mt-2 text-xl font-semibold text-[var(--text)]">Bring Dashboard V2 online</h2>
          <p className="mt-2 text-sm text-muted">
            Dashboard V2 is the primary interface now. Add the runtime credentials here to unlock the full B.U.D.D.Y stack.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <label className="flex flex-col gap-2">
            <span className="text-[10px] uppercase tracking-[0.2em] text-muted font-orbitron">Gemini API Key</span>
            <input
              value={geminiApiKey}
              onChange={(event) => setGeminiApiKey(event.target.value)}
              className="rounded-lg bg-black/20 px-3 py-3 text-sm text-white outline-none border border-[var(--border)]"
              placeholder="BUDDY_GEMINI_API_KEY"
            />
          </label>
          <label className="flex flex-col gap-2">
            <span className="text-[10px] uppercase tracking-[0.2em] text-muted font-orbitron">Telegram Bot Token</span>
            <input
              value={telegramBotToken}
              onChange={(event) => setTelegramBotToken(event.target.value)}
              className="rounded-lg bg-black/20 px-3 py-3 text-sm text-white outline-none border border-[var(--border)]"
              placeholder="Optional"
            />
          </label>
          <label className="flex flex-col gap-2">
            <span className="text-[10px] uppercase tracking-[0.2em] text-muted font-orbitron">Telegram Username</span>
            <input
              value={telegramUsername}
              onChange={(event) => setTelegramUsername(event.target.value)}
              className="rounded-lg bg-black/20 px-3 py-3 text-sm text-white outline-none border border-[var(--border)]"
              placeholder="Optional"
            />
          </label>
          <label className="flex flex-col gap-2">
            <span className="text-[10px] uppercase tracking-[0.2em] text-muted font-orbitron">Telegram User ID</span>
            <input
              value={telegramUserId}
              onChange={(event) => setTelegramUserId(event.target.value)}
              className="rounded-lg bg-black/20 px-3 py-3 text-sm text-white outline-none border border-[var(--border)]"
              placeholder="Optional"
            />
          </label>
        </div>

        <div className="mt-4 min-h-[18px] text-[11px] text-amber-300">{localError || error}</div>

        <div className="mt-4 flex justify-end">
          <button
            type="submit"
            className="rounded-lg px-5 py-3 text-[11px] font-orbitron uppercase tracking-[0.25em]"
            style={{
              background: "linear-gradient(135deg, rgba(92,246,255,0.18), rgba(92,246,255,0.06))",
              border: "1px solid rgba(92,246,255,0.28)",
              color: "#5cf6ff",
            }}
          >
            Save And Launch
          </button>
        </div>
      </motion.form>
    </motion.div>
  );
}
