import type { JobAnalysis, TokenResponse, User, UserProfile } from "./types";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "";

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {},
  token?: string,
): Promise<T> {
  const headers = new Headers(options.headers);
  if (options.body) headers.set("Content-Type", "application/json");
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const response = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (response.status === 204) return undefined as T;
  const body = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = body?.detail;
    const message =
      typeof detail === "string"
        ? detail
        : Array.isArray(detail)
          ? detail.map((item) => item.msg).join(" ")
          : "요청을 처리하지 못했습니다.";
    throw new ApiError(response.status, message);
  }
  return body as T;
}

export const api = {
  register: (email: string, password: string) =>
    request<User>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),

  login: (email: string, password: string) =>
    request<TokenResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),

  me: (token: string) => request<User>("/users/me", {}, token),

  getProfile: (token: string) =>
    request<UserProfile>("/users/me/profile", {}, token),

  saveProfile: (token: string, resumeMarkdown: string) =>
    request<UserProfile>(
      "/users/me/profile",
      { method: "PUT", body: JSON.stringify({ resume_markdown: resumeMarkdown }) },
      token,
    ),

  deleteProfile: (token: string) =>
    request<void>("/users/me/profile", { method: "DELETE" }, token),

  analyze: (
    token: string,
    input: {
      source_url?: string;
      content?: string;
      consent_to_external_llm: boolean;
    },
  ) =>
    request<JobAnalysis>(
      "/job-analyses",
      { method: "POST", body: JSON.stringify(input) },
      token,
    ),
};
