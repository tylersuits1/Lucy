const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export class ChatApiError extends Error {}

export async function sendChatMessage(message: string): Promise<string> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });
  } catch {
    throw new ChatApiError(`Could not reach Lucy at ${API_BASE_URL}.`);
  }

  if (!response.ok) {
    throw new ChatApiError(`Lucy returned an error (${response.status}).`);
  }

  const data = await response.json();
  return data.reply;
}
