import React from 'react';
import { useCurrentFrame, useVideoConfig } from 'remotion';

export const DataGrid: React.FC = () => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();

  const scanPos = (frame * 5) % height;

  return (
    <div
      style={{
        position: 'absolute',
        width: '100%',
        height: '100%',
        overflow: 'hidden',
        pointerEvents: 'none',
      }}
    >
      {/* Horizontal Grid Lines */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          backgroundImage: 'linear-gradient(rgba(0, 242, 255, 0.05) 1px, transparent 1px)',
          backgroundSize: '100% 40px',
        }}
      />

      {/* Vertical Grid Lines */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          backgroundImage: 'linear-gradient(90deg, rgba(0, 242, 255, 0.05) 1px, transparent 1px)',
          backgroundSize: '40px 100%',
        }}
      />

      {/* Scanning Line */}
      <div
        style={{
          position: 'absolute',
          top: scanPos,
          width: '100%',
          height: '2px',
          background: 'linear-gradient(90deg, transparent, rgba(0, 242, 255, 0.5), transparent)',
          boxShadow: '0 0 15px rgba(0, 242, 255, 0.8)',
        }}
      />

      {/* Random Data Points */}
      {Array.from({ length: 15 }).map((_, i) => {
        const x = (Math.sin(i * 123.45) * 0.5 + 0.5) * width;
        const y = (Math.cos(i * 543.21) * 0.5 + 0.5) * height;
        const opacity = Math.sin((frame + i * 20) / 10) * 0.5 + 0.5;
        
        return (
          <div
            key={i}
            style={{
              position: 'absolute',
              left: x,
              top: y,
              width: '4px',
              height: '4px',
              background: '#00f2ff',
              borderRadius: '50%',
              opacity: opacity * 0.3,
              boxShadow: '0 0 10px #00f2ff',
            }}
          />
        );
      })}
    </div>
  );
};
