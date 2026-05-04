import { useEffect, useRef, useState } from 'react';

export interface TypewriterOptions {
  /** Average ms between characters. Default: 18. */
  speed?: number;
  /** Additional pause (ms) after `.`, `!`, `?`. Default: 140. */
  sentencePause?: number;
  /** Additional pause (ms) after `,`, `;`, `:`, `—`. Default: 60. */
  clausePause?: number;
  /** When false, immediately show the full text (no animation). */
  enabled?: boolean;
}

/**
 * Reveal `text` one character at a time. Restarts whenever `text` changes.
 * When `enabled` flips to false mid-flight, the full text is shown instantly
 * (useful when a message ceases to be the "latest" turn).
 *
 * Returns `{ displayed, done }`. Consumers can render a caret while `!done`.
 */
export function useTypewriter(
  text: string,
  options: TypewriterOptions = {},
): { displayed: string; done: boolean } {
  const {
    speed = 18,
    sentencePause = 140,
    clausePause = 60,
    enabled = true,
  } = options;

  const [displayed, setDisplayed] = useState(() => (enabled ? '' : text));
  const [done, setDone] = useState(!enabled);

  // Keep the latest text in a ref so a stopped animation can still settle
  // on the correct final string when `enabled` flips off.
  const textRef = useRef(text);
  textRef.current = text;

  useEffect(() => {
    if (!enabled) {
      setDisplayed(textRef.current);
      setDone(true);
      return;
    }

    setDisplayed('');
    setDone(false);

    let i = 0;
    let cancelled = false;
    let timer: number | undefined;

    const tick = () => {
      if (cancelled) return;
      const full = textRef.current;
      i += 1;
      setDisplayed(full.slice(0, i));

      if (i >= full.length) {
        setDone(true);
        return;
      }

      const prev = full[i - 1];
      let delay = speed;
      if (prev === '.' || prev === '!' || prev === '?') delay += sentencePause;
      else if (prev === ',' || prev === ';' || prev === ':' || prev === '—') {
        delay += clausePause;
      }
      timer = window.setTimeout(tick, delay);
    };

    // Small leading delay so the first character doesn't race the mount.
    timer = window.setTimeout(tick, 80);

    return () => {
      cancelled = true;
      if (timer !== undefined) window.clearTimeout(timer);
    };
  }, [text, enabled, speed, sentencePause, clausePause]);

  return { displayed, done };
}
