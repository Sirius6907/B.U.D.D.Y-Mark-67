import React from 'react';
import { interpolate, useCurrentFrame, useVideoConfig } from 'remotion';

export const Background: React.FC = () => {
  const frame = useCurrentFrame();
  useVideoConfig();

  // Move the grid slightly to create a slow "floating" effect
  const translateY = interpolate(frame, [0, 300], [0, -50], {
    extrapolateRight: 'clamp',
  });

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        backgroundColor: '#050505',
        overflow: 'hidden',
      }}
    >
      {/* Grid Pattern */}
      <div
        style={{
          position: 'absolute',
          inset: -100,
          backgroundImage: `
            linear-gradient(to right, rgba(0, 242, 255, 0.05) 1px, transparent 1px),
            linear-gradient(to bottom, rgba(0, 242, 255, 0.05) 1px, transparent 1px)
          `,
          backgroundSize: '40px 40px',
          transform: `translateY(${translateY}px) perspective(1000px) rotateX(20deg)`,
          opacity: 0.5,
        }}
      />

      {/* Glowing Orbs */}
      <div
        style={{
          position: 'absolute',
          top: '20%',
          left: '10%',
          width: '300px',
          height: '300px',
          background: 'radial-gradient(circle, rgba(0, 242, 255, 0.1) 0%, transparent 70%)',
          filter: 'blur(50px)',
        }}
      />
      <div
        style={{
          position: 'absolute',
          bottom: '20%',
          right: '10%',
          width: '400px',
          height: '400px',
          background: 'radial-gradient(circle, rgba(255, 0, 255, 0.05) 0%, transparent 70%)',
          filter: 'blur(60px)',
        }}
      />
    </div>
  );
};
