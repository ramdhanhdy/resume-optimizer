import React from 'react';
import { motion } from 'framer-motion';

export const ProcessingAnimation: React.FC = () => {
  return (
    <div className="relative w-[300px] h-[300px] flex items-center justify-center text-accent pointer-events-none">
      {/* Core Glow */}
      <motion.div
        className="absolute w-32 h-32 bg-accent/20 rounded-full blur-xl"
        animate={{
          scale: [1, 1.2, 1],
          opacity: [0.3, 0.6, 0.3],
        }}
        transition={{
          duration: 3,
          repeat: Infinity,
          ease: "easeInOut",
        }}
      />

      <svg
        viewBox="0 0 300 300"
        className="w-full h-full absolute inset-0"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        {/* Outer Dashed Ring - Slow CW Rotation */}
        <motion.circle
          cx="150"
          cy="150"
          r="140"
          stroke="currentColor"
          strokeWidth="1"
          strokeOpacity="0.2"
          strokeDasharray="10 10"
          initial={{ rotate: 0 }}
          animate={{ rotate: 360 }}
          transition={{
            duration: 30,
            repeat: Infinity,
            ease: "linear",
          }}
          style={{ transformOrigin: "150px 150px" }}
        />

        {/* Middle Tech Ring - Medium CCW Rotation */}
        <motion.circle
          cx="150"
          cy="150"
          r="110"
          stroke="currentColor"
          strokeWidth="2"
          strokeOpacity="0.4"
          strokeDasharray="40 180" // Creates segments
          strokeLinecap="round"
          initial={{ rotate: 360 }}
          animate={{ rotate: 0 }}
          transition={{
            duration: 15,
            repeat: Infinity,
            ease: "linear",
          }}
          style={{ transformOrigin: "150px 150px" }}
        />

        {/* Inner Detailed Ring - Fast CW Rotation */}
        <motion.circle
          cx="150"
          cy="150"
          r="80"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeOpacity="0.6"
          strokeDasharray="2 8"
          initial={{ rotate: 0 }}
          animate={{ rotate: 360 }}
          transition={{
            duration: 8,
            repeat: Infinity,
            ease: "linear",
          }}
          style={{ transformOrigin: "150px 150px" }}
        />

        {/* Orbiting Particles */}
        <motion.g
          initial={{ rotate: 0 }}
          animate={{ rotate: 360 }}
          transition={{
            duration: 10,
            repeat: Infinity,
            ease: "linear",
          }}
          style={{ transformOrigin: "150px 150px" }}
        >
            <circle cx="260" cy="150" r="3" fill="currentColor" fillOpacity="0.8" />
            <circle cx="40" cy="150" r="3" fill="currentColor" fillOpacity="0.8" />
        </motion.g>
        
        <motion.g
          initial={{ rotate: 45 }}
          animate={{ rotate: -315 }}
          transition={{
            duration: 15,
            repeat: Infinity,
            ease: "linear",
          }}
          style={{ transformOrigin: "150px 150px" }}
        >
            <circle cx="220" cy="150" r="2" fill="currentColor" fillOpacity="0.6" />
        </motion.g>
      </svg>

      {/* Inner Pulse Circle (Solid) */}
      <motion.div
        className="absolute w-20 h-20 border border-accent/50 rounded-full"
        animate={{
          scale: [1, 1.1, 1],
          opacity: [0.5, 1, 0.5],
          borderWidth: ["1px", "2px", "1px"]
        }}
        transition={{
          duration: 2,
          repeat: Infinity,
          ease: "easeInOut",
        }}
      />
      
      {/* Center Point */}
      <div className="absolute w-2 h-2 bg-accent rounded-full" />
    </div>
  );
};
