import React from 'react';
import { interpolate, useCurrentFrame, spring, useVideoConfig, AbsoluteFill } from 'remotion';

export const BuddyCore: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const rotation = interpolate(frame, [0, 300], [0, 360]);
  const rotationFast = interpolate(frame, [0, 300], [0, 720]);
  const rotationSlow = interpolate(frame, [0, 300], [0, 180]);
  
  const scale = spring({
    frame,
    fps,
    config: {
      damping: 12,
    },
  });

  const pulse = Math.sin(frame / 10) * 0.05 + 1;
  const glow = Math.sin(frame / 15) * 0.2 + 0.8;

  return (
    <div
      style={{
        position: 'absolute',
        top: '50%',
        left: '50%',
        transform: `translate(-50%, -50%) scale(${scale * pulse})`,
        width: '400px',
        height: '400px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      {/* Outer Decorative Ring */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          border: '1px solid rgba(0, 242, 255, 0.1)',
          borderRadius: '50%',
        }}
      />

      {/* Pulsing Aura */}
      <div
        style={{
          position: 'absolute',
          width: '110%',
          height: '110%',
          background: 'radial-gradient(circle, rgba(0, 242, 255, 0.05) 0%, transparent 70%)',
          borderRadius: '50%',
          transform: `scale(${1 + (pulse - 1) * 2})`,
          opacity: glow * 0.3,
        }}
      />

      {/* Rotating Dashed Ring */}
      <div
        style={{
          position: 'absolute',
          width: '95%',
          height: '95%',
          border: '2px dashed rgba(0, 242, 255, 0.2)',
          borderRadius: '50%',
          transform: `rotate(${rotationSlow}deg)`,
        }}
      />

      {/* Hexagon Grid Pattern */}
      {[0, 60, 120, 180, 240, 300].map((deg) => (
        <div
          key={deg}
          style={{
            position: 'absolute',
            width: '85%',
            height: '2px',
            background: `linear-gradient(90deg, transparent, rgba(0, 242, 255, ${0.3 * glow}), transparent)`,
            transform: `rotate(${deg + rotationFast}deg)`,
          }}
        >
          <div style={{ position: 'absolute', right: 0, width: '4px', height: '4px', backgroundColor: '#00f2ff', borderRadius: '50%', boxShadow: '0 0 10px #00f2ff' }} />
        </div>
      ))}

      {/* Primary HUD Ring */}
      <div
        style={{
          position: 'absolute',
          width: '75%',
          height: '75%',
          border: '6px double rgba(0, 242, 255, 0.5)',
          borderRadius: '50%',
          borderTopColor: 'transparent',
          borderBottomColor: 'transparent',
          transform: `rotate(${-rotationFast * 0.5}deg)`,
          boxShadow: `0 0 30px rgba(0, 242, 255, ${0.4 * glow})`,
        }}
      />

      {/* Secondary Orbiting Ring */}
      <div
        style={{
          position: 'absolute',
          width: '60%',
          height: '60%',
          border: '2px solid rgba(0, 242, 255, 0.7)',
          borderRadius: '50%',
          borderLeftColor: 'transparent',
          borderRightColor: 'transparent',
          transform: `rotate(${rotation * 2}deg)`,
        }}
      >
        {/* Orbiting Satellite Dots */}
        <div style={{ position: 'absolute', top: '-5px', left: '50%', width: '10px', height: '10px', backgroundColor: '#00f2ff', borderRadius: '50%', boxShadow: '0 0 15px #00f2ff' }} />
      </div>

      {/* Core Plasma Sphere */}
      <div
        style={{
          width: '40%',
          height: '40%',
          background: 'radial-gradient(circle, #00f2ff 0%, #0066ff 60%, #001a33 100%)',
          borderRadius: '50%',
          boxShadow: `0 0 ${60 * glow}px rgba(0, 242, 255, 1.0), inset 0 0 30px rgba(255, 255, 255, 0.6)`,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'white',
          zIndex: 10,
          border: '3px solid rgba(255, 255, 255, 0.4)',
        }}
      >
        <div 
          style={{ 
            fontFamily: 'JetBrains Mono',
            fontSize: '10px',
            opacity: 0.7,
            letterSpacing: '2px',
            marginBottom: '2px'
          }}
        >
          OS KERNEL
        </div>
        <div 
          style={{ 
            fontFamily: 'JetBrains Mono',
            fontSize: '36px',
            fontWeight: 'bold',
            textShadow: '0 0 15px rgba(255, 255, 255, 0.9)',
            letterSpacing: '3px'
          }}
        >
          BUDDY
        </div>
        <div 
          style={{ 
            fontFamily: 'JetBrains Mono',
            fontSize: '12px',
            color: '#00f2ff',
            marginTop: '2px'
          }}
        >
          MK-67
        </div>
      </div>

      {/* Light Flare */}
      <div
        style={{
          position: 'absolute',
          width: '140%',
          height: '1px',
          background: 'linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.6), transparent)',
          transform: `rotate(${rotationFast * 1.2}deg)`,
          filter: 'blur(1px)',
          opacity: glow * 0.4,
        }}
      />
      <div
        style={{
          position: 'absolute',
          width: '1px',
          height: '140%',
          background: 'linear-gradient(0deg, transparent, rgba(255, 255, 255, 0.6), transparent)',
          transform: `rotate(${rotationFast * 1.2}deg)`,
          filter: 'blur(1px)',
          opacity: glow * 0.4,
        }}
      />
    </div>
  );
};

