"use client";

import { Message } from "@/hooks/useHeillChat";
import { ItineraryCard } from "./ItineraryCard";

interface Props {
  message: Message;
}

export function MessageBubble({ message }: Props) {
  const isUser = message.role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-4`}>
      {!isUser && (
        <div className="mr-3 mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-heill-600 text-white text-xs font-bold select-none">
          H
        </div>
      )}
      <div className={`max-w-[80%] ${isUser ? "items-end" : "items-start"} flex flex-col gap-2`}>
        <div
          className={
            isUser
              ? "rounded-2xl rounded-tr-sm bg-heill-600 px-4 py-3 text-sm text-white"
              : "rounded-2xl rounded-tl-sm bg-white border border-slate-200 px-4 py-3 text-sm text-slate-800 shadow-sm"
          }
        >
          {message.content ? (
            <p className="whitespace-pre-wrap leading-relaxed">{message.content}</p>
          ) : (
            <span className="inline-flex gap-1">
              <span className="h-2 w-2 rounded-full bg-slate-400 animate-bounce" style={{ animationDelay: "0ms" }} />
              <span className="h-2 w-2 rounded-full bg-slate-400 animate-bounce" style={{ animationDelay: "150ms" }} />
              <span className="h-2 w-2 rounded-full bg-slate-400 animate-bounce" style={{ animationDelay: "300ms" }} />
            </span>
          )}
        </div>

        {message.itinerary && (
          <ItineraryCard data={message.itinerary as any} />
        )}
      </div>
    </div>
  );
}
