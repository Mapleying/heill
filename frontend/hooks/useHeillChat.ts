"use client";

import { useCallback, useRef, useState } from "react";
import { v4 as uuidv4 } from "uuid";

export interface ToolStatus {
  id: string;
  tool: string;
  status: "running" | "done" | "error";
  error?: string;
}

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  itinerary?: object;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL
  ? `${process.env.NEXT_PUBLIC_API_URL}/chat`
  : "/api/chat";

function extractItinerary(text: string): object | null {
  const match = text.match(/```json\s*([\s\S]*?)\s*```/);
  if (!match) return null;
  try {
    const parsed = JSON.parse(match[1]);
    return "itineraries" in parsed ? parsed : null;
  } catch {
    return null;
  }
}

function stripJsonBlock(text: string): string {
  return text.replace(/```json[\s\S]*?```/g, "").trim();
}

export function useHeillChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [toolStatuses, setToolStatuses] = useState<ToolStatus[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const sessionIdRef = useRef<string | null>(
    typeof window !== "undefined" ? localStorage.getItem("heill_session_id") : null
  );

  const clearTools = useCallback(() => setToolStatuses([]), []);

  const sendMessage = useCallback(async (text: string) => {
    if (!text.trim() || isLoading) return;

    const userMsg: Message = { id: uuidv4(), role: "user", content: text };
    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);
    clearTools();

    const assistantId = uuidv4();
    let assistantText = "";

    setMessages((prev) => [
      ...prev,
      { id: assistantId, role: "assistant", content: "" },
    ]);

    try {
      const resp = await fetch(API_BASE, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionIdRef.current,
          message: text,
        }),
      });

      if (!resp.ok || !resp.body) {
        throw new Error(`HTTP ${resp.status}`);
      }

      const reader = resp.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() ?? "";

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          const raw = line.slice(6).trim();
          if (!raw) continue;

          let evt: Record<string, string>;
          try {
            evt = JSON.parse(raw);
          } catch {
            continue;
          }

          switch (evt.type) {
            case "session_id":
              sessionIdRef.current = evt.session_id;
              localStorage.setItem("heill_session_id", evt.session_id);
              break;

            case "text":
              assistantText += evt.content;
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantId ? { ...m, content: assistantText } : m
                )
              );
              break;

            case "tool_start":
              setToolStatuses((prev) => [
                ...prev,
                { id: evt.tool_id, tool: evt.tool, status: "running" },
              ]);
              break;

            case "tool_end":
              setToolStatuses((prev) =>
                prev.map((t) =>
                  t.id === evt.tool_id ? { ...t, status: "done" } : t
                )
              );
              break;

            case "tool_error":
              setToolStatuses((prev) =>
                prev.map((t) =>
                  t.id === evt.tool_id
                    ? { ...t, status: "error", error: evt.error }
                    : t
                )
              );
              break;

            case "done": {
              const itinerary = extractItinerary(assistantText);
              const displayText = itinerary
                ? stripJsonBlock(assistantText)
                : assistantText;
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantId
                    ? { ...m, content: displayText, itinerary: itinerary ?? undefined }
                    : m
                )
              );
              break;
            }

            case "error":
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantId
                    ? { ...m, content: `Error: ${evt.content}` }
                    : m
                )
              );
              break;
          }
        }
      }
    } catch (err) {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantId
            ? { ...m, content: "Something went wrong. Please try again." }
            : m
        )
      );
    } finally {
      setIsLoading(false);
    }
  }, [isLoading, clearTools]);

  const reset = useCallback(() => {
    sessionIdRef.current = null;
    localStorage.removeItem("heill_session_id");
    setMessages([]);
    setToolStatuses([]);
  }, []);

  return { messages, toolStatuses, isLoading, sendMessage, reset };
}
