import { useEffect, useRef, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { ArrowUp, Loader2, Mic, Plus } from 'lucide-react';
import { useConversation } from './ConversationContext';
import { ChoicePills } from './ChoicePills';
import { AttachedFilePill, FileDropZone } from './FileDropZone';
import { AuthPills } from './AuthPills';
import { ReviewActions } from './ReviewActions';
import { uploadResume, MOCK_STREAM } from '@/lib/api';
import { cn } from '@/lib/cn';
import type { AgentUI } from './types';

/**
 * Floating pill-shaped composer. Renders:
 *   - Contextual module(s) above the pill (choices / drop-zone / auth).
 *   - A text input at the bottom for free-form replies.
 *
 * Which module appears is driven by `activeAgent.ui.kind`. If `kind === 'none'`
 * or the script has ended, the text input still shows (disabled) so the layout
 * stays stable.
 */
export function Composer() {
  const { state, activeAgent, submit } = useConversation();
  const [value, setValue] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);

  const ui: AgentUI = activeAgent?.ui ?? { kind: 'none' };
  const scriptEnded = !state.currentStepId;
  const isProcessing = state.phase === 'PROCESSING';
  const disabled = isProcessing || !activeAgent || scriptEnded || uploading;

  // Reset composer state whenever the active step changes.
  useEffect(() => {
    setValue('');
    setFile(null);
    setUploadError(null);
    setUploading(false);
  }, [activeAgent?.id]);

  // Auto-size the textarea.
  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
  }, [value]);

  const canSubmit = (() => {
    if (disabled) return false;
    switch (ui.kind) {
      case 'text':
        return value.trim().length > 0;
      case 'file':
        return !!file || value.trim().length > 0;
      case 'choices':
        return ui.allowFreeText ? value.trim().length > 0 : false;
      case 'auth':
      case 'review':
      case 'none':
        return false;
    }
  })();

  const handleTextSubmit = async () => {
    if (!canSubmit) return;

    // File-step special case: if the user attached a file and didn't type
    // text themselves, extract the text server-side before submitting so
    // downstream phases (and /api/pipeline/start) have `resume_text` ready.
    if (ui.kind === 'file' && file && !value.trim()) {
      // Mock stream mode doesn't actually care about the contents.
      if (MOCK_STREAM) {
        submit({ text: `[mock] ${file.name}`, file });
        return;
      }
      try {
        setUploading(true);
        setUploadError(null);
        const { text } = await uploadResume(file);
        submit({ text, file });
      } catch (err) {
        const msg = err instanceof Error ? err.message : 'Upload failed';
        setUploadError(msg);
      } finally {
        setUploading(false);
      }
      return;
    }

    submit({ text: value, file });
  };

  return (
    <div className="flex flex-col items-center gap-3">
      {/* Inline upload error surface (file step only) */}
      <AnimatePresence>
        {uploadError && (
          <motion.p
            key="upload-err"
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="text-[12px] text-red-500"
          >
            {uploadError}
          </motion.p>
        )}
      </AnimatePresence>

      {/* Contextual module slot */}
      <div className="w-full">
        <AnimatePresence mode="popLayout">
          {ui.kind === 'choices' && (
            <ChoicePills
              key={`choices-${activeAgent?.id}`}
              choices={ui.choices}
              disabled={disabled}
              onPick={(c) => submit({ text: c.label, choiceValue: c.value })}
            />
          )}

          {ui.kind === 'file' && !file && (
            <motion.div key={`file-${activeAgent?.id}`} className="w-full">
              <FileDropZone
                accept={ui.accept}
                onPickFile={(f) => setFile(f)}
              />
            </motion.div>
          )}

          {ui.kind === 'auth' && (
            <AuthPills
              key={`auth-${activeAgent?.id}`}
              providers={ui.providers}
              disabled={disabled}
              onPick={() => {
                // Phase 1/2 placeholder — just advance the script.
                submit({ text: 'Signed in', choiceValue: 'signed_in' });
              }}
            />
          )}

          {ui.kind === 'review' && (
            <motion.div
              key={`review-${activeAgent?.id}`}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 4 }}
              transition={{ duration: 0.4, ease: [0.2, 0.7, 0.2, 1] }}
              className="w-full"
            >
              <ReviewActions review={state.data.review} />
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Ambient pill-shaped input bar — hidden entirely during the Phase 5
          reveal so the contextual action pills above are the only input. */}
      {ui.kind !== 'review' && (
      <motion.form
        layout
        onSubmit={(e) => {
          e.preventDefault();
          handleTextSubmit();
        }}
        className={cn(
          'glass-sky flex w-full items-center gap-2 rounded-full pl-2 pr-3 py-1.5',
          'soft-shadow-lg ring-1 ring-sky-200/60 transition',
          'focus-within:ring-sky-300/80',
          disabled && !isProcessing && 'opacity-70',
          // Locked look during PROCESSING: flatten, desaturate, and dim.
          isProcessing &&
            'pointer-events-none opacity-60 saturate-50 ring-ink-200/60',
        )}
      >
        {/* Attach — always visible, opens native picker */}
        <button
          type="button"
          onClick={() => {
            const input = document.querySelector<HTMLInputElement>(
              'input[type="file"]',
            );
            input?.click();
          }}
          disabled={ui.kind !== 'file'}
          className={cn(
            'flex h-9 w-9 shrink-0 items-center justify-center rounded-full',
            'text-ink-500 transition hover:bg-white/60 hover:text-ink-800',
            'disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:bg-transparent',
          )}
          aria-label="Attach file"
        >
          <Plus className="h-4 w-4" strokeWidth={2} />
        </button>

        {/* Attached-file pill (inline) */}
        {file && (
          <div className="shrink-0">
            <AttachedFilePill file={file} onRemove={() => setFile(null)} />
          </div>
        )}

        <textarea
          ref={textareaRef}
          rows={1}
          disabled={disabled || ui.kind === 'auth'}
          placeholder={placeholderFor(ui, state.phase)}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              handleTextSubmit();
            }
          }}
          className={cn(
            'no-scrollbar block min-h-[28px] w-full resize-none bg-transparent',
            'px-1 py-1.5 text-[15px] leading-6 text-ink-900',
            'placeholder:text-ink-400 focus:outline-none',
          )}
        />

        {/* Right-side ambient controls */}
        <AnimatePresence mode="wait" initial={false}>
          {uploading ? (
            <motion.div
              key="uploading"
              initial={{ opacity: 0, scale: 0.85 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.85 }}
              className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-ink-900 text-white"
              aria-label="Uploading"
            >
              <Loader2 className="h-4 w-4 animate-spin" strokeWidth={2} />
            </motion.div>
          ) : canSubmit ? (
            <motion.button
              key="send"
              type="submit"
              initial={{ opacity: 0, scale: 0.85 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.85 }}
              transition={{ duration: 0.15 }}
              className={cn(
                'flex h-8 w-8 shrink-0 items-center justify-center rounded-full',
                'bg-ink-900 text-white transition hover:bg-ink-700',
              )}
              aria-label="Send"
            >
              <ArrowUp className="h-4 w-4" strokeWidth={2.25} />
            </motion.button>
          ) : (
            <motion.div
              key="ambient"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex shrink-0 items-center gap-1 pr-1 text-[13px] text-ink-500"
            >
              <span className="hidden select-none sm:inline">Fast</span>
              <button
                type="button"
                aria-label="Voice input"
                className="ml-1 flex h-8 w-8 items-center justify-center rounded-full text-ink-500 hover:bg-white/60 hover:text-ink-800"
              >
                <Mic className="h-4 w-4" strokeWidth={1.75} />
              </button>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.form>
      )}
    </div>
  );
}

function placeholderFor(ui: AgentUI, phase: string): string {
  if (phase === 'PROCESSING') return 'Optimizing…';
  switch (ui.kind) {
    case 'text':
      return ui.placeholder ?? 'Ask your co-pilot…';
    case 'file':
      return ui.placeholder ?? 'or paste it directly…';
    case 'choices':
      return ui.placeholder ?? 'Ask your co-pilot…';
    case 'auth':
      return 'Pick a sign-in option above…';
    case 'review':
      // Never rendered (the input bar is hidden in review mode), but
      // required to make the switch exhaustive.
      return '';
    case 'none':
      return 'Ask your co-pilot…';
  }
}
