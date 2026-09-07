"use client";

import { useEffect, useRef, useState } from "react";
import { ChatApiError, sendChatMessage, uploadFile } from "@/lib/api";

type Message = {
  role: "user" | "assistant" | "error" | "upload";
  text: string;
};

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isBusy, setIsBusy] = useState(false);
  const scrollAnchorRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    scrollAnchorRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    const text = input.trim();
    if (!text || isBusy) return;

    setMessages((prev) => [...prev, { role: "user", text }]);
    setInput("");
    setIsBusy(true);

    try {
      const reply = await sendChatMessage(text);
      setMessages((prev) => [...prev, { role: "assistant", text: reply }]);
    } catch (err) {
      const text = err instanceof ChatApiError ? err.message : "Something went wrong.";
      setMessages((prev) => [...prev, { role: "error", text }]);
    } finally {
      setIsBusy(false);
    }
  }

  async function handleFileSelected(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file || isBusy) return;

    setMessages((prev) => [...prev, { role: "user", text: `📎 ${file.name}` }]);
    setIsBusy(true);

    try {
      const result = await uploadFile(file);
      setMessages((prev) => [
        ...prev,
        {
          role: "upload",
          text: `Filed under **${result.category}**${
            result.tags.length ? ` (${result.tags.join(", ")})` : ""
          }\n${result.summary}`,
        },
      ]);
    } catch (err) {
      const text = err instanceof ChatApiError ? err.message : "Something went wrong.";
      setMessages((prev) => [...prev, { role: "error", text }]);
    } finally {
      setIsBusy(false);
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
            Ask Lucy anything about the household, or attach a file to file it away.
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
                      : message.role === "upload"
                        ? "bg-amber-100 text-amber-900 dark:bg-amber-950 dark:text-amber-200"
                        : "bg-zinc-200 text-zinc-900 dark:bg-zinc-800 dark:text-zinc-50"
                }`}
              >
                {message.text}
              </div>
            </div>
          ))}
          {isBusy && (
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
          ref={fileInputRef}
          type="file"
          accept=".pdf,.docx,.txt,.md,.png,.jpg,.jpeg"
          onChange={handleFileSelected}
          hidden
        />
        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          disabled={isBusy}
          aria-label="Attach a file"
          className="rounded-full w-10 h-10 flex items-center justify-center bg-zinc-200 dark:bg-zinc-800 text-zinc-900 dark:text-zinc-50 disabled:opacity-40"
        >
          +
        </button>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Message Lucy…"
          disabled={isBusy}
          className="flex-1 rounded-full px-4 py-2 bg-zinc-200 dark:bg-zinc-800 text-zinc-900 dark:text-zinc-50 outline-none disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={isBusy || !input.trim()}
          className="rounded-full px-5 py-2 bg-zinc-900 text-white dark:bg-zinc-50 dark:text-black font-medium disabled:opacity-40"
        >
          Send
        </button>
      </form>
    </div>
  );
}
