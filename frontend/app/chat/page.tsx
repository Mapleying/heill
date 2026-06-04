"use client";

import { useEffect, useRef } from "react";
import { useHeillChat } from "@/hooks/useHeillChat";
import { ChatInput } from "./components/ChatInput";
import { MessageBubble } from "./components/MessageBubble";
import { ToolStatusBanner } from "./components/ToolStatusBanner";

const SUGGESTIONS = [
  "Tennis camp in Spain, August, budget £2000, flying from London, intermediate",
  "Surf retreat in Portugal, beginner, 1 week in September",
  "Golf break in Scotland, 4 nights, flying from Manchester",
  "Ski holiday in the Alps, family of 3, February",
];

export default function ChatPage() {
  const { messages, toolStatuses, isLoading, sendMessage, reset } = useHeillChat();
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, toolStatuses]);

  return (
    <div className="flex h-screen flex-col bg-slate-50">
      {/* Header */}
      <header className="flex items-center justify-between border-b border-slate-200 bg-white px-6 py-4 shadow-sm">
        <div>
          <h1 className="text-xl font-bold text-heill-700">Heill</h1>
          <p className="text-xs text-slate-400">AI Sports Travel Agent</p>
        </div>
        {messages.length > 0 && (
          <button
            onClick={reset}
            className="rounded-lg px-3 py-1.5 text-xs text-slate-500 hover:bg-slate-100 transition-colors"
          >
            New chat
          </button>
        )}
      </header>

      {/* Messages area */}
      <div className="flex-1 overflow-y-auto px-4 py-6 scrollbar-thin">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full gap-8">
            <div className="text-center">
              <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-heill-600 mx-auto">
                <span className="text-2xl font-bold text-white">H</span>
              </div>
              <h2 className="text-2xl font-bold text-slate-800">Where do you want to play?</h2>
              <p className="mt-2 text-slate-500 max-w-sm">
                Tell me your sport, destination, dates, and budget — I'll find you a complete package.
              </p>
            </div>
            <div className="grid grid-cols-1 gap-2 w-full max-w-lg sm:grid-cols-2">
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  onClick={() => sendMessage(s)}
                  className="rounded-xl border border-slate-200 bg-white px-4 py-3 text-left text-sm text-slate-600
                    hover:border-heill-300 hover:bg-heill-50 hover:text-heill-700 transition-colors shadow-sm"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="mx-auto max-w-3xl">
            {messages.map((msg) => (
              <MessageBubble key={msg.id} message={msg} />
            ))}
          </div>
        )}

        {/* Tool status banners */}
        {toolStatuses.length > 0 && (
          <div className="mx-auto max-w-3xl">
            <ToolStatusBanner statuses={toolStatuses} />
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="mx-auto w-full max-w-3xl">
        <ChatInput onSend={sendMessage} disabled={isLoading} />
      </div>
    </div>
  );
}
