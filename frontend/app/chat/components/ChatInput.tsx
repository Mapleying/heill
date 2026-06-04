"use client";

import { KeyboardEvent, useRef, useState } from "react";

interface Props {
  onSend: (text: string) => void;
  disabled?: boolean;
}

export function ChatInput({ onSend, disabled }: Props) {
  const [value, setValue] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const submit = () => {
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setValue("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  const handleKey = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  };

  const handleInput = () => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 200)}px`;
  };

  return (
    <div className="flex items-end gap-3 border-t border-slate-200 bg-white px-4 py-3">
      <textarea
        ref={textareaRef}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKey}
        onInput={handleInput}
        disabled={disabled}
        placeholder="Where do you want to play? e.g. Tennis camp in Spain, August, budget £2000…"
        rows={1}
        className="flex-1 resize-none rounded-xl border border-slate-300 bg-slate-50 px-4 py-3 text-sm
          placeholder:text-slate-400 focus:border-heill-500 focus:bg-white focus:outline-none
          focus:ring-2 focus:ring-heill-500/20 disabled:opacity-50 max-h-[200px] overflow-y-auto"
      />
      <button
        onClick={submit}
        disabled={disabled || !value.trim()}
        aria-label="Send"
        className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-heill-600
          text-white transition-colors hover:bg-heill-700 disabled:opacity-40 disabled:cursor-not-allowed"
      >
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="h-5 w-5">
          <path d="M3.105 2.289a.75.75 0 00-.826.95l1.414 4.925A1.5 1.5 0 005.135 9.25h6.115a.75.75 0 010 1.5H5.135a1.5 1.5 0 00-1.442 1.086l-1.414 4.926a.75.75 0 00.826.95 28.896 28.896 0 0015.293-7.154.75.75 0 000-1.115A28.897 28.897 0 003.105 2.289z" />
        </svg>
      </button>
    </div>
  );
}
