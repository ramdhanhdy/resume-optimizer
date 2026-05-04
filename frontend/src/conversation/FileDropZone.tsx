import {
  forwardRef,
  useCallback,
  useRef,
  useState,
  type DragEvent,
  type KeyboardEvent,
  type Ref,
} from 'react';
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
export const FileDropZone = forwardRef<HTMLInputElement, FileDropZoneProps>(
  function FileDropZone({ accept, onPickFile }, forwardedRef) {
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement | null>(null);

  const setInputRef = useCallback(
    (node: HTMLInputElement | null) => {
      inputRef.current = node;
      assignRef(forwardedRef, node);
    },
    [forwardedRef],
  );

  const activatePicker = useCallback(() => {
    inputRef.current?.click();
  }, []);

  const pickAcceptedFile = useCallback(
    (file: File | null | undefined) => {
      if (!file || !matchesAccept(file, accept)) return;
      onPickFile(file);
    },
    [accept, onPickFile],
  );

  const onDrop = useCallback(
    (e: DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      setDragging(false);
      const file = e.dataTransfer.files?.[0];
      pickAcceptedFile(file);
    },
    [pickAcceptedFile],
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
      onClick={activatePicker}
      onKeyDown={(e: KeyboardEvent<HTMLDivElement>) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          activatePicker();
        }
      }}
      className={cn(
        'group flex cursor-pointer items-center justify-center gap-3',
        'glass-sky rounded-3xl px-5 py-4 text-[14px] text-ink-500',
        'ring-1 ring-dashed ring-sky-200 transition',
        'hover:text-ink-900 hover:ring-sky-300',
        dragging && 'ring-sky-500 text-ink-900 scale-[1.01]',
      )}
      role="button"
      aria-label="Drop a file or click to upload"
      tabIndex={0}
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
        ref={setInputRef}
        type="file"
        accept={accept}
        className="hidden"
        onChange={(e) => {
          const f = e.target.files?.[0];
          pickAcceptedFile(f);
          // reset so the same file can be re-picked later
          e.target.value = '';
        }}
      />
    </motion.div>
  );
});

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

function assignRef<T>(ref: Ref<T> | undefined, value: T | null) {
  if (!ref) return;
  if (typeof ref === 'function') {
    ref(value);
    return;
  }
  ref.current = value;
}

function matchesAccept(file: File, accept?: string): boolean {
  if (!accept?.trim()) return true;

  const fileName = file.name.toLowerCase();
  const mimeType = file.type.toLowerCase();

  return accept
    .split(',')
    .map((part) => part.trim().toLowerCase())
    .filter(Boolean)
    .some((rule) => {
      if (rule.startsWith('.')) {
        return fileName.endsWith(rule);
      }
      if (rule.endsWith('/*')) {
        const prefix = rule.slice(0, -1);
        return mimeType.startsWith(prefix);
      }
      return mimeType === rule;
    });
}
