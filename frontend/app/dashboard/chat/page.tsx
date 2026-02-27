"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { getApiUrl } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

type ChatSession = {
  id: string;
  title: string | null;
  created_at: string;
  updated_at: string;
};

type ChatMessage = {
  id: string;
  role: string;
  content: string;
  created_at: string;
};

function formatTime(iso: string): string {
  try {
    return new Date(iso).toLocaleTimeString(undefined, {
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return "";
  }
}

export default function ChatPage() {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loadingSessions, setLoadingSessions] = useState(true);
  const [loadingMessages, setLoadingMessages] = useState(false);
  const [streamingContent, setStreamingContent] = useState("");
  const [input, setInput] = useState("");
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<AbortController | null>(null);

  const fetchSessions = useCallback(() => {
    setLoadingSessions(true);
    setError(null);
    fetch(getApiUrl("/api/ai/chat/sessions"), { credentials: "include" })
      .then((r) => {
        if (!r.ok) throw new Error("Failed to load sessions");
        return r.json();
      })
      .then((data: ChatSession[]) => setSessions(data))
      .catch((e) => setError(e instanceof Error ? e.message : "Error"))
      .finally(() => setLoadingSessions(false));
  }, []);

  useEffect(() => {
    fetchSessions();
  }, [fetchSessions]);

  useEffect(() => {
    if (!currentSessionId) {
      setMessages([]);
      return;
    }
    setLoadingMessages(true);
    setError(null);
    fetch(getApiUrl(`/api/ai/chat/sessions/${currentSessionId}/messages`), {
      credentials: "include",
    })
      .then((r) => {
        if (!r.ok) throw new Error("Failed to load messages");
        return r.json();
      })
      .then((data: ChatMessage[]) => setMessages(data))
      .catch((e) => setError(e instanceof Error ? e.message : "Error"))
      .finally(() => setLoadingMessages(false));
  }, [currentSessionId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamingContent]);

  async function createSession() {
    setError(null);
    try {
      const res = await fetch(getApiUrl("/api/ai/chat/sessions"), {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
      });
      if (!res.ok) throw new Error("Failed to create session");
      const session: ChatSession = await res.json();
      setSessions((prev) => [session, ...prev]);
      setCurrentSessionId(session.id);
      setMessages([]);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error");
    }
  }

  async function sendMessage() {
    const content = input.trim();
    if (!content || !currentSessionId) return;
    setInput("");
    setMessages((prev) => [
      ...prev,
      {
        id: crypto.randomUUID(),
        role: "user",
        content,
        created_at: new Date().toISOString(),
      },
    ]);
    setStreamingContent("");

    abortRef.current = new AbortController();
    const url = getApiUrl(`/api/ai/chat/sessions/${currentSessionId}/messages`);
    try {
      const res = await fetch(url, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content }),
        signal: abortRef.current.signal,
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error((data as { detail?: string }).detail ?? res.statusText);
      }
      const reader = res.body?.getReader();
      const decoder = new TextDecoder();
      let accumulated = "";
      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          accumulated += decoder.decode(value, { stream: true });
          setStreamingContent(accumulated);
        }
      }
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: accumulated,
          created_at: new Date().toISOString(),
        },
      ]);
      setStreamingContent("");
      fetchSessions();
    } catch (e) {
      if ((e as Error).name === "AbortError") return;
      setError(e instanceof Error ? e.message : "Failed to send");
    } finally {
      abortRef.current = null;
    }
  }

  return (
    <div className="flex h-[calc(100vh-8rem)] gap-4">
      <aside className="flex w-52 shrink-0 flex-col rounded-lg border border-border bg-card">
        <div className="border-b border-border p-2">
          <Button size="sm" className="w-full" onClick={createSession}>
            New chat
          </Button>
        </div>
        <div className="flex-1 overflow-auto p-2">
          {loadingSessions ? (
            <p className="text-sm text-muted-foreground">Loading…</p>
          ) : sessions.length === 0 ? (
            <p className="text-sm text-muted-foreground">No chats yet. Start one above.</p>
          ) : (
            <ul className="space-y-1">
              {sessions.map((s) => (
                <li key={s.id}>
                  <button
                    type="button"
                    onClick={() => setCurrentSessionId(s.id)}
                    className={cn(
                      "w-full rounded-md px-2 py-1.5 text-left text-sm truncate",
                      currentSessionId === s.id
                        ? "bg-sidebar-accent text-sidebar-accent-foreground"
                        : "hover:bg-muted"
                    )}
                  >
                    {s.title || "New chat"}
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      </aside>

      <div className="flex flex-1 flex-col min-w-0 rounded-lg border border-border bg-card">
        {!currentSessionId ? (
          <div className="flex flex-1 items-center justify-center text-muted-foreground">
            Select a chat or create a new one.
          </div>
        ) : (
          <>
            <div className="flex-1 overflow-auto p-4 space-y-4">
              {error && (
                <div className="rounded-md border border-destructive/50 bg-destructive/10 px-3 py-2 text-sm text-destructive">
                  {error}
                </div>
              )}
              {loadingMessages ? (
                <p className="text-sm text-muted-foreground">Loading messages…</p>
              ) : (
                <>
                  {messages.map((m) => (
                    <div
                      key={m.id}
                      className={cn(
                        "rounded-lg px-3 py-2 max-w-[85%]",
                        m.role === "user"
                          ? "ml-auto bg-primary text-primary-foreground"
                          : "bg-muted"
                      )}
                    >
                      <p className="text-sm whitespace-pre-wrap">{m.content}</p>
                      <p className="text-xs opacity-70 mt-1">{formatTime(m.created_at)}</p>
                    </div>
                  ))}
                  {streamingContent && (
                    <div className="rounded-lg px-3 py-2 max-w-[85%] bg-muted">
                      <p className="text-sm whitespace-pre-wrap">{streamingContent}</p>
                    </div>
                  )}
                  <div ref={messagesEndRef} />
                </>
              )}
            </div>
            <div className="border-t border-border p-3">
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  sendMessage();
                }}
                className="flex gap-2"
              >
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Type a message…"
                  className="flex-1 rounded-md border border-input bg-background px-3 py-2 text-sm"
                  disabled={!currentSessionId}
                />
                <Button type="submit" disabled={!input.trim() || !currentSessionId}>
                  Send
                </Button>
              </form>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
