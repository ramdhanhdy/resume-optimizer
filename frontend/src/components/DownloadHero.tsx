import { motion, useMotionValue, useTransform, animate } from 'framer-motion';
import { useEffect, useState } from 'react';

interface DownloadHeroProps {
  overallScore: number;
  onRestart: () => void;
}

export default function DownloadHero({
  overallScore,
  onRestart
}: DownloadHeroProps) {
  const [hasAnimated, setHasAnimated] = useState(false);
  const count = useMotionValue(0);
  const rounded = useTransform(count, Math.round);

  // Determine color based on score  - using design system colors
  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-primary';
    if (score >= 60) return 'text-primary';
    return 'text-warning';
  };

  const getCircleColor = (score: number) => {
    if (score >= 80) return 'text-accent';
    if (score >= 60) return 'text-primary';
    return 'text-warning';
  };

  useEffect(() => {
    if (!hasAnimated) {
      const controls = animate(count, overallScore, {
        duration: 2,
        ease: "easeOut"
      });
      setHasAnimated(true);
      return controls.stop;
    }
  }, [overallScore, hasAnimated, count]);

  // Calculate circumference for SVG circle
  const radius = 70;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (overallScore / 100) * circumference;

  return (
    <div className="bg-surface-light border-b border-border-subtle">
      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Top row: Title and actions */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-8">
          <div>
            <motion.h1
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, ease: [0.4, 0.0, 0.2, 1] }}
              className="text-4xl font-semibold text-text-main tracking-tight mb-2"
            >
              Your Resume is Ready
            </motion.h1>
            <motion.p
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.1, duration: 0.4 }}
              className="text-text-main/70 text-sm"
            >
              Review the analysis below and download your optimized resume
            </motion.p>
          </div>

          <motion.button
            initial={{ opacity: 0, x: 10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2, duration: 0.4 }}
            onClick={onRestart}
            className="text-sm font-medium text-primary hover:text-primary/80 transition-colors whitespace-nowrap"
          >
            Start New Application →
          </motion.button>
        </div>

        {/* Score display */}
        <div className="flex justify-center">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.3, duration: 0.5, ease: [0.4, 0.0, 0.2, 1] }}
            className="relative"
          >
            {/* Score circle */}
            <div className="relative w-48 h-48 flex items-center justify-center">
              {/* Background circle */}
              <svg className="absolute inset-0 -rotate-90" width="192" height="192">
                <circle
                  cx="96"
                  cy="96"
                  r={radius}
                  stroke="currentColor"
                  strokeWidth="8"
                  fill="none"
                  className="text-border-subtle"
                />
                {/* Progress circle */}
                <motion.circle
                  cx="96"
                  cy="96"
                  r={radius}
                  stroke="currentColor"
                  strokeWidth="8"
                  fill="none"
                  className={getCircleColor(overallScore)}
                  strokeLinecap="round"
                  initial={{ strokeDashoffset: circumference }}
                  animate={{ strokeDashoffset }}
                  transition={{ duration: 1.5, delay: 0.4, ease: "easeOut" }}
                  style={{
                    strokeDasharray: circumference,
                  }}
                />
              </svg>

              {/* Score text */}
              <div className="text-center z-10">
                <motion.div
                  className={`text-5xl font-semibold ${getScoreColor(overallScore)}`}
                >
                  <motion.span>{rounded}</motion.span>
                  <span className="text-2xl">%</span>
                </motion.div>
                <div className="text-xs text-text-main/60 mt-1">
                  Overall Match
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
}
