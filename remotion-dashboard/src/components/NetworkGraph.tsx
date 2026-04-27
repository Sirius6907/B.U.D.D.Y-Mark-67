import React from 'react';
import { useCurrentFrame, interpolate, spring, useVideoConfig } from 'remotion';

export const NetworkGraph: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const nodes = [
    { x: 200, y: 175, label: "BUDDY_CORE_LXVII", type: 'primary' },
    { x: 100, y: 80, label: "NEURAL_VLM" },
    { x: 300, y: 80, label: "SARVAM_TTS" },
    { x: 80, y: 280, label: "CHROMA_VEC" },
    { x: 320, y: 280, label: "OS_INTEROP" },
    { x: 380, y: 175, label: "SYNC_GATE" },
    { x: 20, y: 175, label: "SEC_PROXY" },
  ];

  const connections = [
    [0, 1], [0, 2], [0, 3], [0, 4], [0, 5], [0, 6],
    [1, 2], [3, 4], [5, 2], [6, 1]
  ];

  return (
    <div
      style={{
        position: 'absolute',
        top: '60px',
        right: '60px',
        width: '440px',
        height: '350px',
        background: 'rgba(0, 5, 10, 0.4)',
        border: '1px solid rgba(0, 242, 255, 0.1)',
        borderTop: '4px solid rgba(0, 242, 255, 0.4)',
        borderRadius: '2px',
        overflow: 'hidden',
        backdropFilter: 'blur(5px)',
      }}
    >
      <div style={{ 
        padding: '10px 15px', 
        fontSize: '10px', 
        color: '#00f2ff', 
        display: 'flex', 
        justifyContent: 'space-between',
        background: 'rgba(0, 242, 255, 0.05)',
        borderBottom: '1px solid rgba(0, 242, 255, 0.1)'
      }}>
        <span style={{ letterSpacing: '2px' }}>NETWORK_TOPOLOGY_0x67</span>
        <span style={{ opacity: 0.5 }}>ACTIVE_NODES: {nodes.length}</span>
      </div>
      
      <svg width="100%" height="100%" style={{ background: 'radial-gradient(circle at center, rgba(0, 242, 255, 0.05) 0%, transparent 70%)' }}>
        {/* Grid lines */}
        {[...Array(10)].map((_, i) => (
          <line key={`h-${i}`} x1="0" y1={i * 40} x2="440" y2={i * 40} stroke="rgba(0, 242, 255, 0.03)" strokeWidth="1" />
        ))}
        {[...Array(12)].map((_, i) => (
          <line key={`v-${i}`} x1={i * 40} y1="0" x2={i * 40} y2="350" stroke="rgba(0, 242, 255, 0.03)" strokeWidth="1" />
        ))}

        {/* Connections */}
        {connections.map(([a, b], i) => {
          const nodeA = nodes[a];
          const nodeB = nodes[b];
          const dashOffset = frame * 1.5;
          
          return (
            <g key={i}>
              <line
                x1={nodeA.x}
                y1={nodeA.y}
                x2={nodeB.x}
                y2={nodeB.y}
                stroke="rgba(0, 242, 255, 0.15)"
                strokeWidth="1"
              />
              <line
                x1={nodeA.x}
                y1={nodeA.y}
                x2={nodeB.x}
                y2={nodeB.y}
                stroke="rgba(0, 242, 255, 0.4)"
                strokeWidth="1.5"
                strokeDasharray="4 20"
                strokeDashoffset={-dashOffset}
              />
              {/* Packet animation */}
              <circle r="2" fill="#fff" style={{ filter: 'drop-shadow(0 0 4px #00f2ff)' }}>
                <animateMotion
                  dur="3s"
                  repeatCount="indefinite"
                  path={`M${nodeA.x},${nodeA.y} L${nodeB.x},${nodeB.y}`}
                  begin={`${i * 0.5}s`}
                />
              </circle>
            </g>
          );
        })}

        {/* Nodes */}
        {nodes.map((node, i) => {
          const pulse = Math.sin((frame + i * 20) / 8) * 2 + 4;
          const isPrimary = node.type === 'primary';
          
          return (
            <g key={i} style={{ filter: 'drop-shadow(0 0 8px rgba(0, 242, 255, 0.5))' }}>
              {isPrimary && (
                <>
                  <circle cx={node.x} cy={node.y} r="15" fill="none" stroke="rgba(0, 242, 255, 0.2)" strokeWidth="1" strokeDasharray="2 2">
                    <animateTransform attributeName="transform" type="rotate" from={`0 ${node.x} ${node.y}`} to={`360 ${node.x} ${node.y}`} dur="10s" repeatCount="indefinite" />
                  </circle>
                  <circle cx={node.x} cy={node.y} r="12" fill="rgba(0, 242, 255, 0.1)" />
                </>
              )}
              <circle
                cx={node.x}
                cy={node.y}
                r={isPrimary ? 6 : pulse}
                fill={isPrimary ? "#fff" : "#00f2ff"}
              />
              <rect 
                x={node.x - 20} 
                y={node.y + 12} 
                width="40" 
                height="1" 
                fill="rgba(0, 242, 255, 0.3)" 
              />
              <text
                x={node.x}
                y={node.y + 25}
                fill="#00f2ff"
                textAnchor="middle"
                style={{ 
                  fontSize: isPrimary ? '10px' : '8px', 
                  fontFamily: 'JetBrains Mono', 
                  fontWeight: isPrimary ? 'bold' : 'normal',
                  letterSpacing: '1px'
                }}
              >
                {node.label}
              </text>
            </g>
          );
        })}
      </svg>

      {/* HUD Scanner Line */}
      <div style={{
        position: 'absolute',
        top: 0,
        left: 0,
        width: '100%',
        height: '2px',
        background: 'linear-gradient(to right, transparent, rgba(0, 242, 255, 0.5), transparent)',
        boxShadow: '0 0 10px rgba(0, 242, 255, 0.5)',
        transform: `translateY(${(frame % 150) * (350 / 150)}px)`,
        opacity: 0.3
      }} />
    </div>
  );
};
