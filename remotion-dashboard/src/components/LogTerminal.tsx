import React from 'react';
import { useCurrentFrame } from 'remotion';

const LOGS = [
  "[BOOT] INITIALIZING BUDDY KERNEL MK-67...",
  "[OK] VLM SEMANTIC ENGINE ONLINE",
  "[OK] NEURAL VOICE ROUTER CONNECTED",
  "[OK] RAG VECTOR STORE INDEXED",
  "[WARN] HIGH LATENCY DETECTED IN PRIMARY NODE",
  "[INFO] SHIFTING TO FAST-BRAIN ROUTING",
  "[SEC] FIREWALL HARDENING COMPLETE",
  "[OK] SIRIUS PROTOCOL ACTIVE",
  "[BOOT] ESTABLISHING SECURE TELEGRAM BRIDGE",
  "[OK] BROWSER AUTOMATION ENGINE READY",
  "[INFO] SCANNING LOCAL REPOSITORY...",
  "[OK] 142 FILES INDEXED IN CHROMADB",
  "[INFO] MEMORY CACHE OPTIMIZED",
  "[BOOT] ALL SYSTEMS NOMINAL.",
  "[INFO] AWAITING USER COMMAND...",
  "[EXE] DISPATCHING BROWSER AGENT...",
  "[OK] SEARCH RESULTS RETRIEVED",
  "[INFO] REASONING IN PROGRESS...",
  "[SEC] ENCRYPTION HANDSHAKE SUCCESS",
  "[OK] OS CONTROL INTERFACE LINKED"
];

export const LogTerminal: React.FC = () => {
  const frame = useCurrentFrame();
  
  const visibleLogsCount = Math.floor(frame / 6);
  const displayedLogs = LOGS.slice(0, visibleLogsCount).slice(-10);

  return (
    <div
      style={{
        position: 'absolute',
        bottom: '60px',
        right: '60px',
        width: '440px',
        height: '260px',
        background: 'linear-gradient(135deg, rgba(0, 5, 10, 0.9) 0%, rgba(0, 20, 30, 0.8) 100%)',
        border: '1px solid rgba(0, 242, 255, 0.2)',
        borderRight: '4px solid rgba(0, 242, 255, 0.4)',
        padding: '20px',
        borderRadius: '2px',
        backdropFilter: 'blur(15px)',
        fontFamily: 'JetBrains Mono, monospace',
        fontSize: '11px',
        color: '#00f2ff',
        overflow: 'hidden',
        boxShadow: '0 10px 40px rgba(0, 0, 0, 0.9)',
      }}
    >
      <div style={{ 
        borderBottom: '1px solid rgba(0, 242, 255, 0.1)', 
        marginBottom: '15px', 
        paddingBottom: '8px', 
        fontSize: '10px', 
        fontWeight: 'bold', 
        display: 'flex', 
        justifyContent: 'space-between',
        letterSpacing: '2px',
        color: 'rgba(0, 242, 255, 0.5)'
      }}>
        <span>SYSTEM_KERNEL_LOG // MARK_LXVII</span>
        <span style={{ color: '#00f2ff' }}>ONLINE</span>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column' }}>
        {displayedLogs.map((log, i) => (
          <div key={i} style={{ 
            marginBottom: '6px', 
            opacity: i === displayedLogs.length - 1 ? 1 : 0.4 + (i * 0.05),
            transform: `translateX(${i === displayedLogs.length - 1 ? Math.random() * 2 : 0}px)`
          }}>
            <span style={{ marginRight: '10px', opacity: 0.3 }}>{`> [${(frame - (displayedLogs.length - i) * 6).toString().padStart(4, '0')}]`}</span>
            {log}
          </div>
        ))}
      </div>
      <div style={{ 
        position: 'absolute', 
        bottom: '15px', 
        right: '20px', 
        width: '6px', 
        height: '6px', 
        background: '#00f2ff', 
        borderRadius: '50%',
        boxShadow: '0 0 10px #00f2ff',
        opacity: Math.sin(frame / 3) * 0.5 + 0.5
      }} />
    </div>
  );
};
