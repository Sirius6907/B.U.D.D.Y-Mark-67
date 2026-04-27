"use client";
import { Canvas, useFrame } from "@react-three/fiber";
import { useMemo, useRef } from "react";
import * as THREE from "three";

/* ── Particle Field ──────────────────────────────────────── */
function ParticleField({ count = 600 }: { count?: number }) {
  const ref = useRef<THREE.Points>(null!);
  const positions = useMemo(() => {
    const arr = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      arr[i * 3]     = (Math.random() - 0.5) * 20;
      arr[i * 3 + 1] = (Math.random() - 0.5) * 20;
      arr[i * 3 + 2] = (Math.random() - 0.5) * 20;
    }
    return arr;
  }, [count]);

  const sizes = useMemo(() => {
    const arr = new Float32Array(count);
    for (let i = 0; i < count; i++) arr[i] = Math.random() * 2.5 + 0.5;
    return arr;
  }, [count]);

  useFrame(({ clock }) => {
    if (!ref.current) return;
    ref.current.rotation.y = clock.elapsedTime * 0.015;
    ref.current.rotation.x = Math.sin(clock.elapsedTime * 0.008) * 0.08;
  });

  return (
    <points ref={ref}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" args={[positions, 3]} />
        <bufferAttribute attach="attributes-size" args={[sizes, 1]} />
      </bufferGeometry>
      <pointsMaterial
        color="#5cf6ff"
        size={0.035}
        transparent
        opacity={0.55}
        sizeAttenuation
        depthWrite={false}
        blending={THREE.AdditiveBlending}
      />
    </points>
  );
}

/* ── Energy Rings ────────────────────────────────────────── */
function EnergyRing({ radius, speed, tilt }: { radius: number; speed: number; tilt: number }) {
  const ref = useRef<THREE.Mesh>(null!);
  useFrame(({ clock }) => {
    if (!ref.current) return;
    ref.current.rotation.z = clock.elapsedTime * speed;
    ref.current.rotation.x = tilt;
  });
  return (
    <mesh ref={ref}>
      <torusGeometry args={[radius, 0.005, 16, 128]} />
      <meshBasicMaterial color="#5cf6ff" transparent opacity={0.18} />
    </mesh>
  );
}

/* ── Grid Plane ──────────────────────────────────────────── */
function GridPlane() {
  const ref = useRef<THREE.GridHelper>(null!);
  useFrame(({ clock }) => {
    if (!ref.current) return;
    ref.current.position.y = -3.5;
    ref.current.material.opacity = 0.06 + Math.sin(clock.elapsedTime * 0.3) * 0.02;
  });
  return (
    <gridHelper
      ref={ref as any}
      args={[30, 60, "#5cf6ff", "#5cf6ff"]}
      material-transparent
      material-opacity={0.06}
    />
  );
}

/* ── Nebula Core ─────────────────────────────────────────── */
function NebulaCore() {
  const ref = useRef<THREE.Mesh>(null!);
  useFrame(({ clock }) => {
    if (!ref.current) return;
    const s = 1 + Math.sin(clock.elapsedTime * 0.6) * 0.15;
    ref.current.scale.set(s, s, s);
  });
  return (
    <mesh ref={ref}>
      <sphereGeometry args={[1.2, 32, 32]} />
      <meshBasicMaterial color="#0a1828" transparent opacity={0.25} />
    </mesh>
  );
}

/* ── Background World (exported) ─────────────────────────── */
export default function BackgroundWorld() {
  return (
    <div className="absolute inset-0 z-0">
      <Canvas
        camera={{ position: [0, 0, 8], fov: 60 }}
        dpr={[1, 1.5]}
        gl={{ antialias: false, alpha: true, powerPreference: "high-performance" }}
        style={{ background: "transparent" }}
      >
        <ambientLight intensity={0.15} />
        <ParticleField count={700} />
        <EnergyRing radius={3.0} speed={0.12} tilt={Math.PI / 5} />
        <EnergyRing radius={4.2} speed={-0.08} tilt={-Math.PI / 7} />
        <EnergyRing radius={5.5} speed={0.05} tilt={Math.PI / 3} />
        <GridPlane />
        <NebulaCore />
      </Canvas>
    </div>
  );
}
