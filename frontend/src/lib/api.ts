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
      body: formData,
    });
  } catch {
    throw new ChatApiError(`Could not reach Lucy at ${API_BASE_URL}.`);
  }

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new ChatApiError(body?.detail ?? `Lucy returned an error (${response.status}).`);
  }

  return response.json();
}
