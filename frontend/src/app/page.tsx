"use client";

import { useEffect, useRef, useState } from "react";
import {
  ChatApiError,
  ConversationSummary,
  StoredUser,
  clearSession,
  fetchConversation,
  fetchHistory,
  getStoredUser,
  login,
  sendChatMessage,
  uploadFile,
} from "@/lib/api";

type Message = {
  role: "user" | "assistant" | "error" | "upload";
  text: string;
};

function LoginScreen({ onLoggedIn }: { onLoggedIn: (user: StoredUser) => void }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isBusy, setIsBusy] = useState(false);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    setIsBusy(true);
    try {
      const user = await login(username, password);
      onLoggedIn(user);
    } catch (err) {
      setError(err instanceof ChatApiError ? err.message : "Something went wrong.");
    } finally {
      setIsBusy(false);
    }
  }

  return (
    <div className="flex flex-col items-center justify-center h-dvh bg-zinc-50 dark:bg-black px-4">
      <form onSubmit={handleSubmit} className="flex flex-col gap-3 w-full max-w-xs">
        <h1 className="text-xl font-semibold text-zinc-900 dark:text-zinc-50 text-center mb-2">Lucy</h1>
        <input
          type="text"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          placeholder="Username"
          autoComplete="username"
          className="rounded-lg px-4 py-2 bg-zinc-200 dark:bg-zinc-800 text-zinc-900 dark:text-zinc-50 outline-none"
        />
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Password"
          autoComplete="current-password"
          className="rounded-lg px-4 py-2 bg-zinc-200 dark:bg-zinc-800 text-zinc-900 dark:text-zinc-50 outline-none"
        />
        {error && <p className="text-red-600 dark:text-red-400 text-sm">{error}</p>}
        <button
          type="submit"
          disabled={isBusy || !username || !password}
          className="rounded-lg px-5 py-2 bg-zinc-900 text-white dark:bg-zinc-50 dark:text-black font-medium disabled:opacity-40"
        >
          {isBusy ? "Logging in…" : "Log in"}
        </button>
      </form>
    </div>
  );
}

export default function Home() {
  const [user, setUser] = useState<StoredUser | null>(null);
  const [checkedSession, setCheckedSession] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isBusy, setIsBusy] = useState(false);
  const [conversationId, setConversationId] = useState<number | null>(null);
  const [nextIsShared, setNextIsShared] = useState(false);
  const [history, setHistory] = useState<ConversationSummary[]>([]);
  const [showHistory, setShowHistory] = useState(false);
  const scrollAnchorRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    setUser(getStoredUser());
    setCheckedSession(true);
  }, []);

  useEffect(() => {
    scrollAnchorRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function refreshHistory() {
    try {
      setHistory(await fetchHistory());
    } catch {
      // history panel is a convenience — a failed refresh isn't worth surfacing as a chat error
    }
  }

  function handleLogout() {
    clearSession();
    setUser(null);
    setMessages([]);
    setConversationId(null);
    setHistory([]);
  }

  function handleAuthError(err: unknown): string {
    if (err instanceof ChatApiError) {
      if (err.message.includes("Session expired")) handleLogout();
      return err.message;
    }
    return "Something went wrong.";
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    const text = input.trim();
    if (!text || isBusy) return;

    setMessages((prev) => [...prev, { role: "user", text }]);
    setInput("");
    setIsBusy(true);

    try {
      const result = await sendChatMessage(text, conversationId, nextIsShared);
      setConversationId(result.conversationId);
      setMessages((prev) => [...prev, { role: "assistant", text: result.reply }]);
      refreshHistory();
    } catch (err) {
      setMessages((prev) => [...prev, { role: "error", text: handleAuthError(err) }]);
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
      setMessages((prev) => [...prev, { role: "error", text: handleAuthError(err) }]);
    } finally {
      setIsBusy(false);
    }
  }

  function startNewChat(shared: boolean) {
    setConversationId(null);
    setNextIsShared(shared);
    setMessages([]);
    setShowHistory(false);
  }

  async function openConversation(id: number) {
    setIsBusy(true);
    try {
      const conversation = await fetchConversation(id);
      setConversationId(conversation.id);
      setNextIsShared(conversation.isShared);
      setMessages(conversation.messages.map((m) => ({ role: m.role, text: m.content })));
      setShowHistory(false);
    } catch (err) {
      setMessages((prev) => [...prev, { role: "error", text: handleAuthError(err) }]);
    } finally {
      setIsBusy(false);
    }
  }

  function handleToggleHistory() {
    const next = !showHistory;
    setShowHistory(next);
    if (next) refreshHistory();
  }

  if (!checkedSession) return null;
  if (!user) return <LoginScreen onLoggedIn={setUser} />;

  return (
    <div className="flex flex-col h-dvh bg-zinc-50 dark:bg-black">
      <header className="border-b border-zinc-200 dark:border-zinc-800 px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h1 className="text-lg font-semibold text-zinc-900 dark:text-zinc-50">Lucy</h1>
          <span className="text-xs text-zinc-500 dark:text-zinc-400">{user.displayName}</span>
        </div>
        <div className="flex items-center gap-2 text-sm">
          <button onClick={() => startNewChat(false)} className="text-zinc-600 dark:text-zinc-400 hover:underline">
            + New
          </button>
          <button onClick={() => startNewChat(true)} className="text-zinc-600 dark:text-zinc-400 hover:underline">
            + Family
          </button>
          <button onClick={handleToggleHistory} className="text-zinc-600 dark:text-zinc-400 hover:underline">
            History
          </button>
          <button onClick={handleLogout} className="text-zinc-600 dark:text-zinc-400 hover:underline">
            Log out
          </button>
        </div>
      </header>

      {showHistory && (
        <div className="border-b border-zinc-200 dark:border-zinc-800 px-4 py-2 max-h-40 overflow-y-auto">
          {history.length === 0 ? (
            <p className="text-xs text-zinc-500 dark:text-zinc-400">No conversations yet.</p>
          ) : (
            <ul className="flex flex-col gap-1">
              {history.map((c) => (
                <li key={c.id}>
                  <button
                    onClick={() => openConversation(c.id)}
                    className="text-sm text-left w-full text-zinc-700 dark:text-zinc-300 hover:underline"
                  >
                    {c.isShared ? "👨‍👩‍👧 " : ""}
                    {c.title}
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      <main className="flex-1 overflow-y-auto px-4 py-4">
        {messages.length === 0 && (
          <p className="text-zinc-500 dark:text-zinc-400 text-sm">
            {nextIsShared
              ? "Starting a family chat — your wife will see this thread too."
              : "Ask Lucy anything about the household, or attach a file to file it away."}
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
