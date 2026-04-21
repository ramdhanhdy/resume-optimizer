import { useCallback, useRef, useState } from 'react';
import { motion } from 'framer-motion';
import { UploadCloud } from 'lucide-react';
import { cn } from '@/lib/cn';

interface FileDropZoneProps {
  accept?: string;
  onPickFile: (file: File) => void;
}

/**
 * Minimalist drag-and-drop surface that fades in above the input bar.
 * Clicking it also opens the native file picker.
 */
export function FileDropZone({ accept, onPickFile }: FileDropZoneProps) {
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement | null>(null);

  const onDrop = useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      setDragging(false);
      const file = e.dataTransfer.files?.[0];
      if (file) onPickFile(file);
    },
    [onPickFile],
  );

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 4 }}
      transition={{ duration: 0.28, ease: 'easeOut' }}
      onDragEnter={(e) => {
        e.preventDefault();
        setDragging(true);
      }}
      onDragOver={(e) => {
        e.preventDefault();
        setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={onDrop}
      onClick={() => inputRef.current?.click()}
      className={cn(
        'group flex cursor-pointer items-center justify-center gap-3',
        'glass-sky rounded-3xl px-5 py-4 text-[14px] text-ink-500',
        'ring-1 ring-dashed ring-sky-200 transition',
        'hover:text-ink-900 hover:ring-sky-300',
        dragging && 'ring-sky-500 text-ink-900 scale-[1.01]',
      )}
      role="button"
      aria-label="Drop a file or click to upload"
    >
      <UploadCloud
        className={cn(
          'h-5 w-5 text-ink-400 transition group-hover:text-sky-500',
          dragging && 'text-sky-500',
        )}
        strokeWidth={1.75}
      />
      <span className="font-medium">
        Drop your resume here
        <span className="mx-2 text-ink-300">·</span>
        <span className="text-ink-400">or click to browse</span>
      </span>
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        className="hidden"
        onChange={(e) => {
          const f = e.target.files?.[0];
          if (f) onPickFile(f);
          // reset so the same file can be re-picked later
          e.target.value = '';
        }}
      />
    </motion.div>
  );
}

/**
 * Tiny "attached file" pill that lives inside the input bar once a file
 * has been selected.
 */
export function AttachedFilePill({
  file,
  onRemove,
}: {
  file: File;
  onRemove: () => void;
}) {
  const kb = Math.max(1, Math.round(file.size / 1024));
  return (
    <motion.span
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.9 }}
      className="inline-flex max-w-[16ch] items-center gap-1.5 truncate rounded-full bg-white/70 ring-1 ring-sky-200/60 px-2.5 py-1 text-xs text-ink-700"
    >
      <span className="truncate">{file.name}</span>
      <span className="text-ink-400">{kb}kb</span>
      <button
        type="button"
        onClick={(e) => {
          e.stopPropagation();
          onRemove();
        }}
        className="ml-0.5 text-ink-400 hover:text-ink-700"
        aria-label="Remove attachment"
      >
        ×
      </button>
    </motion.span>
  );
}
