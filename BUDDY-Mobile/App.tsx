import "./src/global.css";
import React, { useEffect, useState, useRef } from 'react';
import { View, Text, Pressable, ScrollView } from './src/tw';
import { StatusBar } from 'expo-status-bar';
import { Canvas, BackdropBlur, Fill, LinearGradient, vec, Circle, BlurMask } from "@shopify/react-native-skia";
import { Mic, Send, MessageSquare, ShieldCheck } from 'lucide-react-native';
import { useSharedValue, withRepeat, withTiming, useDerivedValue, interpolate, withSpring } from 'react-native-reanimated';
import { orchestrator, Message } from './src/core/orchestrator';
import { startRecording, stopRecording, transcribeAudio } from './src/services/stt';

export default function App() {
  const [history, setHistory] = useState<Message[]>([]);
  const [isRecording, setIsRecording] = useState(false);
  const pulse = useSharedValue(0);
  const orbScale = useSharedValue(1);
  const scrollViewRef = useRef<any>(null);

  useEffect(() => {
    pulse.value = withRepeat(withTiming(1, { duration: 2000 }), -1, true);
    orchestrator.setUpdateListener((newHistory) => {
      setHistory(newHistory);
      setTimeout(() => scrollViewRef.current?.scrollToEnd({ animated: true }), 100);
    });
  }, []);

  const handleMicPress = async () => {
    if (isRecording) {
      setIsRecording(false);
      orbScale.value = withSpring(1);
      const base64 = await stopRecording();
      if (base64) {
        const text = await transcribeAudio(base64);
        if (text) {
          await orchestrator.processInput(text);
        }
      }
    } else {
      setIsRecording(true);
      orbScale.value = withSpring(1.4);
      await startRecording();
    }
  };

  const radius = useDerivedValue(() => {
    return interpolate(pulse.value, [0, 1], [60, 75]) * orbScale.value;
  });

  const opacity = useDerivedValue(() => {
    return interpolate(pulse.value, [0, 1], [0.3, 0.6]);
  });

  return (
    <View className="flex-1 bg-background items-center justify-center">
      <StatusBar style="light" />
      
      <View className="absolute inset-0">
        <Canvas style={{ flex: 1 }}>
          <Fill>
            <LinearGradient
              start={vec(0, 0)}
              end={vec(400, 800)}
              colors={["#0f172a", "#1e1b4b", "#0f172a"]}
            />
          </Fill>
        </Canvas>
      </View>

      <View className="w-full h-full px-6 pt-16 pb-10">
        {/* Header */}
        <View className="flex-row justify-between items-center mb-8">
          <View>
            <Text className="text-secondary text-[10px] tracking-[0.3em] font-bold uppercase opacity-80">Mark-67 Active</Text>
            <Text className="text-white text-3xl font-bold">B.U.D.D.Y</Text>
          </View>
          <View className="w-10 h-10 rounded-full bg-white/5 border border-white/10 items-center justify-center">
            <ShieldCheck color="#8b5cf6" size={20} />
          </View>
        </View>

        {/* Conversation History */}
        <View className="flex-1 mb-6 rounded-3xl overflow-hidden border border-white/10 bg-white/5">
           <Canvas style={{ position: 'absolute', inset: 0 }}>
            <BackdropBlur blur={10}>
               <Fill color="rgba(255, 255, 255, 0.02)" />
            </BackdropBlur>
          </Canvas>
          <ScrollView 
            ref={scrollViewRef}
            className="flex-1 p-4" 
            contentContainerClassName="gap-4 pb-10"
          >
            {history.length === 0 ? (
              <View className="flex-1 items-center justify-center py-20 opacity-30">
                <MessageSquare color="white" size={48} />
                <Text className="text-white mt-4 text-center">Awaiting neural input...</Text>
              </View>
            ) : (
              history.map((msg, idx) => (
                <View key={idx} className={`max-w-[85%] p-4 rounded-2xl ${msg.role === 'user' ? 'bg-primary/20 self-end border border-primary/30' : 'bg-white/10 self-start border border-white/20'}`}>
                   <Text className={`text-[10px] font-bold mb-1 uppercase tracking-tighter ${msg.role === 'user' ? 'text-primary' : 'text-secondary'}`}>
                      {msg.role}
                   </Text>
                   <Text className="text-white text-sm leading-5">{msg.content}</Text>
                </View>
              ))
            )}
          </ScrollView>
        </View>

        {/* Control Center */}
        <View className="h-48 flex-row items-center justify-between gap-4">
           <View className="flex-1 h-full rounded-3xl border border-white/10 bg-white/5 p-4 justify-between">
              <View>
                 <Text className="text-slate-500 text-[10px] uppercase tracking-widest">Status</Text>
                 <Text className="text-secondary font-bold">{isRecording ? "Listening..." : "Standby"}</Text>
              </View>
              <View className="h-1.5 w-full bg-white/10 rounded-full overflow-hidden">
                  <View className={`h-full bg-secondary ${isRecording ? 'w-full' : 'w-1/3'}`} />
              </View>
           </View>

           <Pressable 
             onPress={handleMicPress}
             className={`w-32 h-full rounded-3xl items-center justify-center border ${isRecording ? 'bg-primary border-primary' : 'bg-white/10 border-white/10'}`}
           >
              <Canvas style={{ position: 'absolute', width: 120, height: 120 }}>
                <Circle cx={60} cy={60} r={radius} color="#8b5cf6" opacity={opacity}>
                  <BlurMask blur={20} style="normal" />
                </Circle>
              </Canvas>
              <Mic color="white" size={32} strokeWidth={2} />
           </Pressable>
        </View>

        <View className="mt-8 items-center">
          <Text className="text-slate-600 text-[9px] tracking-[0.4em] uppercase">Sirius Neural Bridge // v1.0.0-Mobile</Text>
        </View>
      </View>
    </View>
  );
}


