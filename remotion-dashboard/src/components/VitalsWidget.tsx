import React from 'react';
import { interpolate, useCurrentFrame, spring, useVideoConfig } from 'remotion';

interface VitalProps {
  label: string;
  value: string;
  delay: number;
  data: number[];
}

const VitalGraph: React.FC<{ data: number[] }> = ({ data }) => {
  const frame = useCurrentFrame();
  
  const points = data.map((val, i) => {
    const x = (i / (data.length - 1)) * 100;
    const y = 100 - val;
    return `${x},${y}`;
  }).join(' ');

  const progress = interpolate(frame % 300, [0, 300], [0, 100]);

  return (
    <svg width="100%" height="30" viewBox="0 0 100 100" preserveAspectRatio="none">
      <polyline
        fill="none"
        stroke="#00f2ff"
        strokeWidth="2"
        points={points}
        style={{
          strokeDasharray: '1000',
          strokeDashoffset: '0',
        }}
      />
      <rect x={progress} y="0" width="1" height="100" fill="rgba(255, 255, 255, 0.3)" />
    </svg>
  );
};

const Vital: React.FC<VitalProps> = ({ label, value, delay, data }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const opacity = spring({
    frame: frame - delay,
    fps,
  });

  const slide = interpolate(opacity, [0, 1], [20, 0]);

  return (
    <div
      style={{
        opacity,
        transform: `translateY(${slide}px)`,
        marginBottom: '20px',
        background: 'linear-gradient(90deg, rgba(0, 242, 255, 0.08) 0%, transparent 100%)',
        padding: '12px 18px',
        borderRadius: '4px',
        borderLeft: '4px solid #00f2ff',
        backdropFilter: 'blur(5px)',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      {/* Background Grid */}
      <div style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', opacity: 0.1, backgroundImage: 'radial-gradient(#00f2ff 1px, transparent 1px)', backgroundSize: '10px 10px' }} />
      
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: '8px', position: 'relative' }}>
        <div style={{ fontSize: '11px', color: 'rgba(0, 242, 255, 0.7)', textTransform: 'uppercase', letterSpacing: '2px', fontWeight: 'bold' }}>
          {label}
        </div>
        <div style={{ fontSize: '18px', fontWeight: 'bold', fontFamily: 'JetBrains Mono', color: '#00f2ff', textShadow: '0 0 10px rgba(0, 242, 255, 0.5)' }}>
          {value}
        </div>
      </div>
      <VitalGraph data={data} />
    </div>
  );
};

export const VitalsWidget: React.FC = () => {
  const frame = useCurrentFrame();
  
  // Simulated dynamic values
  const cpuVal = (45 + Math.sin(frame / 20) * 15 + Math.random() * 2).toFixed(1);
  const ramVal = (7.42 + Math.sin(frame / 60) * 0.15).toFixed(2);
  const netVal = (1.2 + Math.cos(frame / 30) * 0.4).toFixed(1);

  // Simulated data points with more variance
  const generateData = (seed: number, base: number) => 
    Array.from({ length: 30 }, (_, i) => base + Math.sin((frame + i * 8) / seed) * 25 + (Math.random() * 5));

  return (
    <div style={{ position: 'absolute', top: '60px', left: '60px', width: '320px', zIndex: 50 }}>
      <div style={{ color: 'rgba(0, 242, 255, 0.4)', fontSize: '10px', marginBottom: '15px', letterSpacing: '4px' }}>TELEMETRY_STREAM_V3.0</div>
      <Vital label="CPU_LOAD" value={`${cpuVal}%`} delay={5} data={generateData(12, 40)} />
      <Vital label="MEM_ALLOC" value={`${ramVal} GB`} delay={15} data={generateData(22, 60)} />
      <Vital label="NET_TRAFFIC" value={`${netVal} MB/s`} delay={25} data={generateData(18, 30)} />
      <Vital label="SYS_STABILITY" value="OPTIMAL" delay={35} data={generateData(45, 80)} />
    </div>
  );
};

