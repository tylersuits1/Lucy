"use client";

import { useEffect, useRef, useState } from "react";
import { ChatApiError, sendChatMessage } from "@/lib/api";

type Message = {
  role: "user" | "assistant" | "error";
  text: string;
};

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const scrollAnchorRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollAnchorRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    const text = input.trim();
    if (!text || isSending) return;

    setMessages((prev) => [...prev, { role: "user", text }]);
    setInput("");
    setIsSending(true);

    try {
      const reply = await sendChatMessage(text);
      setMessages((prev) => [...prev, { role: "assistant", text: reply }]);
    } catch (err) {
      const text = err instanceof ChatApiError ? err.message : "Something went wrong.";
      setMessages((prev) => [...prev, { role: "error", text }]);
    } finally {
      setIsSending(false);
    }
  }

  return (
    <div className="flex flex-col h-dvh bg-zinc-50 dark:bg-black">
      <header className="border-b border-zinc-200 dark:border-zinc-800 px-4 py-3">
        <h1 className="text-lg font-semibold text-zinc-900 dark:text-zinc-50">Lucy</h1>
      </header>

      <main className="flex-1 overflow-y-auto px-4 py-4">
        {messages.length === 0 && (
          <p className="text-zinc-500 dark:text-zinc-400 text-sm">
            Ask Lucy anything about the household.
          </p>
        )}
        <div className="flex flex-col gap-3 max-w-2xl mx-auto">
          {messages.map((message, index) => (
            <div
              key={index}
              className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`rounded-2xl px-4 py-2 max-w-[80%] whitespace-pre-wrap text-sm ${
                  message.role === "user"
                    ? "bg-zinc-900 text-white dark:bg-zinc-50 dark:text-black"
                    : message.role === "error"
                      ? "bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-200"
                      : "bg-zinc-200 text-zinc-900 dark:bg-zinc-800 dark:text-zinc-50"
                }`}
              >
                {message.text}
              </div>
            </div>
          ))}
          {isSending && (
            <div className="flex justify-start">
              <div className="rounded-2xl px-4 py-2 bg-zinc-200 text-zinc-500 dark:bg-zinc-800 dark:text-zinc-400 text-sm">
                Thinking…
              </div>
            </div>
          )}
          <div ref={scrollAnchorRef} />
        </div>
      </main>

      <form
        onSubmit={handleSubmit}
        className="border-t border-zinc-200 dark:border-zinc-800 p-3 flex gap-2 max-w-2xl w-full mx-auto"
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Message Lucy…"
          disabled={isSending}
          className="flex-1 rounded-full px-4 py-2 bg-zinc-200 dark:bg-zinc-800 text-zinc-900 dark:text-zinc-50 outline-none disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={isSending || !input.trim()}
          className="rounded-full px-5 py-2 bg-zinc-900 text-white dark:bg-zinc-50 dark:text-black font-medium disabled:opacity-40"
        >
          Send
        </button>
      </form>
    </div>
  );
}
