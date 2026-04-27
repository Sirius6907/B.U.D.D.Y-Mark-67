"use client";
import dynamic from "next/dynamic";
import { useState, useCallback, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useDashboardSocket } from "@/lib/use-dashboard-socket";
import { R3FErrorBoundary } from "@/components/r3f-error-boundary";
import TopBar from "@/components/top-bar";
import CoreOrb from "@/components/core-orb";
import TelemetryPanel from "@/components/telemetry-panel";
import LogTerminal from "@/components/log-terminal";
import CommandConsole from "@/components/command-console";
import ApprovalModal from "@/components/approval-modal";
import BootSequence from "@/components/boot-sequence";
import BootAudioController from "@/components/boot-audio-controller";
import ScanLines from "@/components/scan-lines";
import HudOverlay from "@/components/hud-overlay";
import SetupGate from "@/components/setup-gate";
import ShutdownSequence from "@/components/shutdown-sequence";

const BackgroundWorld = dynamic(() => import("@/components/background-world"), { ssr: false });

export default function DashboardPage() {
  const {
    snapshot,
    connectionStatus,
    commandState,
    shutdownFarewell,
    sendCommand,
    sendApproval,
    submitConfig,
    notifyBootComplete,
    closeWindow,
  } =
    useDashboardSocket();
  const [booted, setBooted] = useState(false);
  const [shutdownAnimating, setShutdownAnimating] = useState(false);
  const shutdownTriggeredRef = useRef(false);

  const handleBootComplete = useCallback(() => {
    notifyBootComplete();
    setBooted(true);
  }, [notifyBootComplete]);
  const setupRequired = Boolean(snapshot.runtimeStatus.setupRequired);
  const runtimeReady = Boolean(snapshot.runtimeStatus.runtimeReady);

  useEffect(() => {
    if (shutdownFarewell && !shutdownTriggeredRef.current) {
      shutdownTriggeredRef.current = true;
      setShutdownAnimating(true);
    }
  }, [shutdownFarewell]);

  return (
    <div className="relative w-screen h-screen overflow-hidden">
      <BootAudioController active={!booted} />
      <AnimatePresence>
        {!booted && <BootSequence connectionStatus={connectionStatus} onBootComplete={handleBootComplete} />}
      </AnimatePresence>

      <R3FErrorBoundary>
        <BackgroundWorld />
      </R3FErrorBoundary>

      <HudOverlay />
      <ScanLines />

      <motion.div
        className="relative z-10 flex flex-col h-full"
        initial={{ opacity: 0 }}
        animate={{ opacity: booted ? 1 : 0 }}
        transition={{ duration: 0.8, delay: 0.2 }}
      >
        <TopBar
          connectionStatus={connectionStatus}
          phase={snapshot.state.phase}
          systemStatus={snapshot.state.status}
          muted={snapshot.state.muted}
        />

        <div className="flex-1 flex items-stretch gap-4 px-5 py-3 overflow-hidden">
          <motion.div
            className="w-72 shrink-0"
            initial={{ opacity: 0, x: -30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
          >
            <TelemetryPanel telemetry={snapshot.telemetry} />
          </motion.div>

          <motion.div
            className="flex-1 flex items-center justify-center"
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.8, delay: 0.4 }}
          >
            <CoreOrb
              phase={snapshot.state.phase}
              voiceLevel={snapshot.voiceActivity.level}
              muted={snapshot.state.muted}
            />
          </motion.div>

          <motion.div
            className="w-80 shrink-0"
            initial={{ opacity: 0, x: 30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
          >
            <LogTerminal logs={snapshot.logs} />
          </motion.div>
        </div>

        <div className="px-5 pb-4">
          <CommandConsole
            onSend={sendCommand}
            disabled={!runtimeReady}
            deliveryState={commandState}
            muted={snapshot.state.muted}
          />
        </div>
      </motion.div>

      {snapshot.approvalRequest && <ApprovalModal request={snapshot.approvalRequest} onRespond={sendApproval} />}
      {setupRequired && (
        <SetupGate
          error={String(snapshot.runtimeStatus.configError || "")}
          onSubmit={submitConfig}
        />
      )}
      <AnimatePresence>
        {shutdownAnimating && shutdownFarewell ? (
          <ShutdownSequence farewell={shutdownFarewell} onComplete={closeWindow} />
        ) : null}
      </AnimatePresence>
    </div>
  );
}
