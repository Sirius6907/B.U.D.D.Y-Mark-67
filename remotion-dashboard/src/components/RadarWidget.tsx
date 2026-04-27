import React from 'react';
import { interpolate, useCurrentFrame } from 'remotion';

export const RadarWidget: React.FC = () => {
  const frame = useCurrentFrame();

  const rotation = interpolate(frame, [0, 120], [0, 360]);

  return (
    <div
      style={{
        position: 'absolute',
        bottom: '50px',
        left: '350px',
        width: '180px',
        height: '180px',
        background: 'rgba(0, 242, 255, 0.03)',
        borderRadius: '50%',
        border: '1px solid rgba(0, 242, 255, 0.2)',
        overflow: 'hidden',
        boxShadow: 'inset 0 0 20px rgba(0, 242, 255, 0.1)',
      }}
    >
      <div style={{ position: 'absolute', top: '10px', width: '100%', textAlign: 'center', fontSize: '8px', color: 'rgba(0, 242, 255, 0.5)', textTransform: 'uppercase', letterSpacing: '1px' }}>
        Radar Sweep // S-1
      </div>

      {/* Scanning Line */}
      <div
        style={{
          position: 'absolute',
          width: '50%',
          height: '2px',
          background: 'linear-gradient(to left, #00f2ff, transparent)',
          top: '50%',
          left: '50%',
          transformOrigin: 'left center',
          transform: `rotate(${rotation}deg)`,
          boxShadow: '0 0 10px #00f2ff',
        }}
      />

      {/* Sweep Overlay */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          background: `conic-gradient(from ${rotation - 90}deg, rgba(0, 242, 255, 0.2) 0deg, transparent 90deg)`,
          borderRadius: '50%',
        }}
      />

      {/* Grid Rings */}
      <div style={{ position: 'absolute', inset: '25%', border: '1px solid rgba(0, 242, 255, 0.1)', borderRadius: '50%' }} />
      <div style={{ position: 'absolute', inset: '50%', border: '1px solid rgba(0, 242, 255, 0.1)', borderRadius: '50%' }} />
      <div style={{ position: 'absolute', inset: '0', border: '1px solid rgba(0, 242, 255, 0.2)', borderRadius: '50%' }} />

      {/* Crosshair */}
      <div style={{ position: 'absolute', top: '50%', left: '0', width: '100%', height: '1px', background: 'rgba(0, 242, 255, 0.1)' }} />
      <div style={{ position: 'absolute', top: '0', left: '50%', width: '1px', height: '100%', background: 'rgba(0, 242, 255, 0.1)' }} />

      {/* Blips */}
      <div
        style={{
          position: 'absolute',
          top: '30%',
          left: '60%',
          width: '6px',
          height: '6px',
          backgroundColor: '#00f2ff',
          borderRadius: '50%',
          boxShadow: '0 0 10px #00f2ff',
          opacity: Math.sin(frame / 5) * 0.5 + 0.5,
        }}
      />
      <div
        style={{
          position: 'absolute',
          top: '70%',
          left: '20%',
          width: '4px',
          height: '4px',
          backgroundColor: '#ff3b3b',
          borderRadius: '50%',
          boxShadow: '0 0 10px #ff3b3b',
          opacity: Math.cos(frame / 7) * 0.5 + 0.5,
        }}
      />
    </div>
  );
};

