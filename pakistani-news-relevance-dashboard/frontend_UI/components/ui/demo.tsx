"use client";

import React from "react";
import NeuralBackground from "@/components/ui/flow-field-background";
import { TiltCard } from "@/components/ui/be-ui-tilt-card";
import SpotlightCard from "@/components/ui/spotlight-card";

/**
 * Neural Hero Showcase - Fullscreen Flow-Field background
 */
export function NeuralHeroDemo() {
  return (
    <div className="relative w-full h-screen bg-black">
      <NeuralBackground 
        color="#818cf8" // Indigo-400
        trailOpacity={0.1} // Lower = longer trails
        speed={0.8}
        particleCount={600}
      />
    </div>
  );
}

/**
 * Premium 3D Tilt Card Showcase
 */
export function TiltCardPreview() {
  return (
    <div className="flex items-center justify-center p-6 bg-slate-950 min-h-[400px]">
      <TiltCard className="w-[280px] border border-border bg-card p-8 text-white">
        <div className="text-xs uppercase tracking-wider text-muted-foreground">Premium</div>
        <h3 className="mt-2 text-2xl font-semibold text-foreground">Tilt me</h3>
        <p className="mt-3 text-sm text-muted-foreground">Move your cursor across the card to see 3D tilt + glare.</p>
      </TiltCard>
    </div>
  );
}

/**
 * Premium Spotlight Card Showcase (Cursor-Tracking Glow & Outer Glow Shadow)
 */
export function SpotlightCardPreview() {
  return (
    <div className="flex flex-col items-center justify-center p-12 bg-slate-100 min-h-[400px] gap-8">
      <div className="flex gap-6 flex-wrap justify-center">
        <SpotlightCard className="w-[300px]" spotlightColor="rgba(99, 102, 241, 0.1)" borderColor="rgba(99, 102, 241, 0.45)">
          <div className="text-xs uppercase tracking-wider text-indigo-600 font-semibold">AI Matcher</div>
          <h3 className="mt-2 text-xl font-bold text-slate-800">Spotlight Spotlight</h3>
          <p className="mt-2 text-sm text-slate-500">Hover here to see the dynamic purple border spotlight tracking and glowing shadows.</p>
        </SpotlightCard>
        
        <SpotlightCard className="w-[300px]" spotlightColor="rgba(16, 185, 129, 0.1)" borderColor="rgba(16, 185, 129, 0.45)">
          <div className="text-xs uppercase tracking-wider text-emerald-600 font-semibold">Active Metrics</div>
          <h3 className="mt-2 text-xl font-bold text-slate-800">Emerald Glow</h3>
          <p className="mt-2 text-sm text-slate-500">This spotlight card is configured with custom emerald green indicators for success states.</p>
        </SpotlightCard>
      </div>
    </div>
  );
}
