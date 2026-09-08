const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
const TOKEN_KEY = "lucy_token";
const USER_KEY = "lucy_user";

export class ChatApiError extends Error {}

export type StoredUser = { userId: number; username: string; displayName: string };

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function getStoredUser(): StoredUser | null {
  if (typeof window === "undefined") return null;
  const raw = window.localStorage.getItem(USER_KEY);
  return raw ? (JSON.parse(raw) as StoredUser) : null;
}

export function clearSession(): void {
  window.localStorage.removeItem(TOKEN_KEY);
  window.localStorage.removeItem(USER_KEY);
}

function authHeaders(): Record<string, string> {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function parseErrorDetail(response: Response, fallback: string): Promise<string> {
  const body = await response.json().catch(() => null);
  return body?.detail ?? fallback;
}

export async function login(username: string, password: string): Promise<StoredUser> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });
  } catch {
    throw new ChatApiError(`Could not reach Lucy at ${API_BASE_URL}.`);
  }

  if (!response.ok) {
    throw new ChatApiError(await parseErrorDetail(response, `Login failed (${response.status}).`));
  }

  const data = await response.json();
  const user: StoredUser = { userId: data.user_id, username: data.username, displayName: data.display_name };
  window.localStorage.setItem(TOKEN_KEY, data.access_token);
  window.localStorage.setItem(USER_KEY, JSON.stringify(user));
  return user;
}

export type ChatResult = { reply: string; conversationId: number };

export async function sendChatMessage(
  message: string,
  conversationId: number | null,
  isShared: boolean
): Promise<ChatResult> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify({ message, conversation_id: conversationId, is_shared: isShared }),
    });
  } catch {
    throw new ChatApiError(`Could not reach Lucy at ${API_BASE_URL}.`);
  }

  if (response.status === 401) throw new ChatApiError("Session expired. Please log in again.");
  if (!response.ok) throw new ChatApiError(await parseErrorDetail(response, `Lucy returned an error (${response.status}).`));

  const data = await response.json();
  return { reply: data.reply, conversationId: data.conversation_id };
}

export type UploadResult = {
  category: string;
  filename: string;
  tags: string[];
  summary: string;
  chunks_ingested: number;
};

export async function uploadFile(file: File): Promise<UploadResult> {
  const formData = new FormData();
  formData.append("file", file);

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/upload`, {
      method: "POST",
      headers: authHeaders(),
      body: formData,
    });
  } catch {
    throw new ChatApiError(`Could not reach Lucy at ${API_BASE_URL}.`);
  }

  if (response.status === 401) throw new ChatApiError("Session expired. Please log in again.");
  if (!response.ok) throw new ChatApiError(await parseErrorDetail(response, `Lucy returned an error (${response.status}).`));

  return response.json();
}

export type ConversationSummary = {
  id: number;
  title: string;
  isShared: boolean;
  createdAt: number;
};

export async function fetchHistory(): Promise<ConversationSummary[]> {
  const response = await fetch(`${API_BASE_URL}/history`, { headers: authHeaders() });
  if (response.status === 401) throw new ChatApiError("Session expired. Please log in again.");
  if (!response.ok) throw new ChatApiError(await parseErrorDetail(response, `Lucy returned an error (${response.status}).`));
  const data = await response.json();
  return data.map((c: { id: number; title: string; is_shared: boolean; created_at: number }) => ({
    id: c.id,
    title: c.title,
    isShared: c.is_shared,
    createdAt: c.created_at,
  }));
}

export type HistoryMessage = { role: "user" | "assistant"; content: string; createdAt: number };

export async function fetchConversation(
  conversationId: number
): Promise<{ id: number; title: string; isShared: boolean; messages: HistoryMessage[] }> {
  const response = await fetch(`${API_BASE_URL}/history/${conversationId}`, { headers: authHeaders() });
  if (response.status === 401) throw new ChatApiError("Session expired. Please log in again.");
  if (!response.ok) throw new ChatApiError(await parseErrorDetail(response, `Lucy returned an error (${response.status}).`));
  const data = await response.json();
  return {
    id: data.id,
    title: data.title,
    isShared: data.is_shared,
    messages: data.messages.map((m: { role: string; content: string; created_at: number }) => ({
      role: m.role,
      content: m.content,
      createdAt: m.created_at,
    })),
  };
}
