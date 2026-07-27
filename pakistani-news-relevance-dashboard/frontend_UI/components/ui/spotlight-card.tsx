"use client";

import React, { useRef, useState, MouseEvent } from "react";
import { cn } from "@/lib/utils";

interface SpotlightCardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  className?: string;
  /**
   * Radial gradient color inside the card.
   * Default: very soft Indigo.
   */
  spotlightColor?: string;
  /**
   * Color illuminating the card border.
   */
  borderColor?: string;
  /**
   * Diameter of the spotlight glow in pixels.
   */
  glowSize?: number;
}

export default function SpotlightCard({
  children,
  className,
  spotlightColor = "rgba(99, 102, 241, 0.08)",
  borderColor = "rgba(99, 102, 241, 0.3)",
  glowSize = 240,
  ...props
}: SpotlightCardProps) {
  const cardRef = useRef<HTMLDivElement>(null);
  const [coords, setCoords] = useState({ x: 0, y: 0 });
  const [isHovered, setIsHovered] = useState(false);

  const handleMouseMove = (e: MouseEvent<HTMLDivElement>) => {
    if (!cardRef.current) return;
    const rect = cardRef.current.getBoundingClientRect();
    setCoords({
      x: e.clientX - rect.left,
      y: e.clientY - rect.top,
    });
  };

  return (
    <div
      ref={cardRef}
      onMouseMove={handleMouseMove}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      className={cn(
        "relative rounded-2xl border border-slate-200/80 bg-white p-6 overflow-hidden transition-all duration-300",
        isHovered ? "shadow-xl border-transparent" : "shadow-md",
        className
      )}
      style={props.style}
      {...props}
    >
      {/* Outer shadow glow behind card */}
      {isHovered && (
        <div
          className="pointer-events-none absolute -inset-[20px] -z-10 transition-opacity duration-300 filter blur-xl opacity-70"
          style={{
            background: `radial-gradient(${glowSize}px circle at ${coords.x + 20}px ${coords.y + 20}px, rgba(99, 102, 241, 0.12), transparent 70%)`,
          }}
        />
      )}

      {/* Internal background spotlight */}
      {isHovered && (
        <div
          className="pointer-events-none absolute inset-0 transition-opacity duration-300"
          style={{
            background: `radial-gradient(${glowSize}px circle at ${coords.x}px ${coords.y}px, ${spotlightColor}, transparent 80%)`,
          }}
        />
      )}

      {/* Hover-tracking illuminated border using mask composite */}
      {isHovered && (
        <div
          className="pointer-events-none absolute -inset-[1px] rounded-2xl transition-opacity duration-300"
          style={{
            padding: "1px",
            background: `radial-gradient(${glowSize * 0.9}px circle at ${coords.x}px ${coords.y}px, ${borderColor}, transparent 60%)`,
            WebkitMask: "linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0)",
            WebkitMaskComposite: "dest-out",
            maskComposite: "exclude",
          }}
        />
      )}

      {/* Content wrapper */}
      <div className="relative z-10">{children}</div>
    </div>
  );
}
