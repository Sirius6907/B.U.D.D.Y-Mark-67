import React from 'react';
import { AbsoluteFill, useCurrentFrame, interpolate } from 'remotion';
import { Background } from './components/Background';
import { BuddyCore } from './components/BuddyCore';
import { VitalsWidget } from './components/VitalsWidget';
import { RadarWidget } from './components/RadarWidget';
import { DataGrid } from './components/DataGrid';
import { LogTerminal } from './components/LogTerminal';
import { NetworkGraph } from './components/NetworkGraph';

export const MyComposition: React.FC = () => {
  const frame = useCurrentFrame();
  
  const glitchOpacity = Math.random() > 0.98 ? 0.3 : 0;
  const vignetteOpacity = interpolate(frame, [0, 30], [1, 0.4]);

  return (
    <AbsoluteFill style={{ backgroundColor: '#00050a', color: 'white', overflow: 'hidden' }}>
      {/* Background Layer */}
      <Background />
      <DataGrid />

      {/* Atmospheric Glow */}
      <div style={{
        position: 'absolute',
        top: '50%',
        left: '50%',
        width: '800px',
        height: '800px',
        background: 'radial-gradient(circle, rgba(0, 242, 255, 0.05) 0%, transparent 70%)',
        transform: 'translate(-50%, -50%)',
        pointerEvents: 'none',
      }} />

      {/* Main Core */}
      <BuddyCore />

      {/* Left HUD */}
      <VitalsWidget />
      <RadarWidget />

      {/* Right HUD */}
      <NetworkGraph />
      <LogTerminal />

      {/* Top Header */}
      <div style={{
        position: 'absolute',
        top: '30px',
        left: '50%',
        transform: 'translateX(-50%)',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: '5px',
        zIndex: 100
      }}>
        <div style={{ fontSize: '10px', color: '#00f2ff', opacity: 0.5, letterSpacing: '8px' }}>NEURAL_INTERFACE_READY</div>
        <div style={{ width: '300px', height: '1px', background: 'linear-gradient(to right, transparent, rgba(0, 242, 255, 0.5), transparent)' }} />
      </div>

      {/* Title Overlay */}
      <div
        style={{
          position: 'absolute',
          bottom: '60px',
          left: '60px',
          fontFamily: 'JetBrains Mono',
          fontSize: '28px',
          color: 'white',
          textTransform: 'uppercase',
          letterSpacing: '6px',
          zIndex: 100,
        }}
      >
        <div style={{ color: '#00f2ff', fontSize: '14px', marginBottom: '8px', opacity: 0.7, fontWeight: 'bold' }}>SIRIUS_PROTO // LXVII</div>
        BUDDY OS <span style={{ color: '#00f2ff', textShadow: '0 0 15px rgba(0, 242, 255, 0.8)' }}>MK-67</span>
      </div>

      {/* Frame Border */}
      <div style={{
        position: 'absolute',
        top: '20px',
        left: '20px',
        right: '20px',
        bottom: '20px',
        border: '1px solid rgba(0, 242, 255, 0.1)',
        pointerEvents: 'none',
      }}>
        {/* Corner Accents */}
        <div style={{ position: 'absolute', top: -1, left: -1, width: '40px', height: '40px', borderTop: '2px solid #00f2ff', borderLeft: '2px solid #00f2ff' }} />
        <div style={{ position: 'absolute', top: -1, right: -1, width: '40px', height: '40px', borderTop: '2px solid #00f2ff', borderRight: '2px solid #00f2ff' }} />
        <div style={{ position: 'absolute', bottom: -1, left: -1, width: '40px', height: '40px', borderBottom: '2px solid #00f2ff', borderLeft: '2px solid #00f2ff' }} />
        <div style={{ position: 'absolute', bottom: -1, right: -1, width: '40px', height: '40px', borderBottom: '2px solid #00f2ff', borderRight: '2px solid #00f2ff' }} />
      </div>

      {/* Cinematic Overlays */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          background: 'radial-gradient(circle, transparent 30%, rgba(0, 0, 0, 0.9) 100%)',
          pointerEvents: 'none',
          opacity: vignetteOpacity,
        }}
      />

      {/* Glitch Effect Overlay */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          backgroundColor: 'rgba(0, 242, 255, 0.05)',
          mixBlendMode: 'overlay',
          opacity: glitchOpacity,
          pointerEvents: 'none',
        }}
      />

      {/* Scanline Texture */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          backgroundImage: 'linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.1) 50%)',
          backgroundSize: '100% 4px',
          pointerEvents: 'none',
          opacity: 0.4
        }}
      />

      {/* Floating Particles Overlay */}
      <div style={{
        position: 'absolute',
        width: '100%',
        height: '100%',
        pointerEvents: 'none',
        opacity: 0.2
      }}>
        {[...Array(50)].map((_, i) => (
          <div key={i} style={{
            position: 'absolute',
            top: `${Math.random() * 100}%`,
            left: `${Math.random() * 100}%`,
            width: '2px',
            height: '2px',
            background: '#00f2ff',
            borderRadius: '50%',
            transform: `translateY(${Math.sin((frame + i * 10) / 20) * 10}px)`,
          }} />
        ))}
      </div>
    </AbsoluteFill>
  );
};

