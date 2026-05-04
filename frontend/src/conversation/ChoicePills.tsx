import { motion } from 'framer-motion';
import type { Choice } from './types';
import { cn } from '@/lib/cn';

interface ChoicePillsProps {
  choices: Choice[];
  onPick: (choice: Choice) => void;
  disabled?: boolean;
}

/**
 * Floating "video-game style" option pills. Each pill staggers in, and
 * fades/scales out together when the user picks one (handled by the
 * AnimatePresence wrapper in the Composer).
 */
export function ChoicePills({ choices, onPick, disabled }: ChoicePillsProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 6, scale: 0.98 }}
      transition={{ duration: 0.3, ease: 'easeOut' }}
      className="flex flex-wrap justify-center gap-2 px-2"
    >
      {choices.map((c, idx) => (
        <motion.button
          key={c.value}
          type="button"
          disabled={disabled}
          onClick={() => onPick(c)}
          initial={{ opacity: 0, y: 8, scale: 0.96 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, scale: 0.9 }}
          transition={{
            duration: 0.25,
            delay: 0.04 * idx,
            ease: [0.2, 0.7, 0.2, 1],
          }}
          whileHover={{ y: -2 }}
          whileTap={{ scale: 0.96 }}
          className={cn(
            'group inline-flex items-baseline gap-2 rounded-full',
            'glass-sky px-4 py-2 text-[14px] text-ink-800',
            'soft-shadow ring-1 ring-sky-200/60 transition',
            'hover:text-ink-900 hover:ring-sky-300',
            'disabled:opacity-50 disabled:pointer-events-none',
          )}
        >
          <span className="font-medium">{c.label}</span>
          {c.hint && (
            <span className="text-[11px] text-ink-400 group-hover:text-ink-500">
              {c.hint}
            </span>
          )}
        </motion.button>
      ))}
    </motion.div>
  );
}
