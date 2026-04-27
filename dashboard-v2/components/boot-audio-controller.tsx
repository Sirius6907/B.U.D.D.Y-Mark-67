"use client";

import { useEffect, useRef } from "react";

interface Props {
  active: boolean;
}

export default function BootAudioController({ active }: Props) {
  const hasPlayedRef = useRef(false);

  useEffect(() => {
    if (!active || hasPlayedRef.current || typeof window === "undefined") {
      return;
    }
    hasPlayedRef.current = true;

    const AudioContextCtor =
      window.AudioContext ||
      (window as typeof window & { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;

    if (!AudioContextCtor) {
      return;
    }

    const context = new AudioContextCtor();
    const master = context.createGain();
    master.gain.value = 0.04;
    master.connect(context.destination);

    const now = context.currentTime;

    const pulse = (start: number, duration: number, frequency: number, type: OscillatorType, gainPeak: number) => {
      const osc = context.createOscillator();
      const gain = context.createGain();
      osc.type = type;
      osc.frequency.setValueAtTime(frequency, start);
      osc.frequency.exponentialRampToValueAtTime(frequency * 1.18, start + duration);
      gain.gain.setValueAtTime(0.0001, start);
      gain.gain.exponentialRampToValueAtTime(gainPeak, start + duration * 0.25);
      gain.gain.exponentialRampToValueAtTime(0.0001, start + duration);
      osc.connect(gain);
      gain.connect(master);
      osc.start(start);
      osc.stop(start + duration);
    };

    const shimmer = (start: number, duration: number) => {
      const osc = context.createOscillator();
      const gain = context.createGain();
      const lfo = context.createOscillator();
      const lfoGain = context.createGain();

      osc.type = "triangle";
      osc.frequency.setValueAtTime(320, start);
      osc.frequency.exponentialRampToValueAtTime(660, start + duration);
      gain.gain.setValueAtTime(0.0001, start);
      gain.gain.exponentialRampToValueAtTime(0.018, start + duration * 0.35);
      gain.gain.exponentialRampToValueAtTime(0.0001, start + duration);

      lfo.type = "sine";
      lfo.frequency.setValueAtTime(8, start);
      lfoGain.gain.setValueAtTime(18, start);
      lfo.connect(lfoGain);
      lfoGain.connect(osc.frequency);

      osc.connect(gain);
      gain.connect(master);

      osc.start(start);
      lfo.start(start);
      osc.stop(start + duration);
      lfo.stop(start + duration);
    };

    pulse(now + 0.05, 0.26, 62, "sawtooth", 0.03);
    pulse(now + 0.33, 0.22, 74, "square", 0.02);
    pulse(now + 0.62, 0.3, 91, "sawtooth", 0.024);
    shimmer(now + 0.85, 0.95);

    const cleanup = window.setTimeout(() => {
      void context.close().catch(() => undefined);
    }, 2600);

    return () => {
      window.clearTimeout(cleanup);
      void context.close().catch(() => undefined);
    };
  }, [active]);

  return null;
}
