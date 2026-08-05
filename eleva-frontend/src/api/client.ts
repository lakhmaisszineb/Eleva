import type { AnalyzeRequestBody, AnalyzeResponse, HealthResponse } from "../types";

const STORAGE_KEY = "eleva_api_base_url";
const DEFAULT_BASE_URL = "http://localhost:8000";

export function getApiBaseUrl(): string {
  return localStorage.getItem(STORAGE_KEY) || DEFAULT_BASE_URL;
}

export function setApiBaseUrl(url: string) {
  localStorage.setItem(STORAGE_KEY, url.replace(/\/+$/, ""));
}

export class ApiError extends Error {
  status: number;
  detail?: unknown;
  constructor(message: string, status: number, detail?: unknown) {
    super(message);
    this.status = status;
    this.detail = detail;
  }
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const base = getApiBaseUrl();
  let res: Response;
  try {
    res = await fetch(`${base}${path}`, {
      ...options,
      headers: { "Content-Type": "application/json", ...(options?.headers || {}) },
    });
  } catch (e) {
    throw new ApiError(
      `Impossible de joindre l'API Eleva sur ${base}. Vérifiez que le backend est démarré (uvicorn api.main:app) et l'URL dans Paramètres.`,
      0
    );
  }

  if (!res.ok) {
    let detail: unknown;
    try {
      detail = await res.json();
    } catch {
      detail = null;
    }
    const message =
      (detail as any)?.detail?.errors?.join(", ") ||
      (detail as any)?.detail ||
      `Erreur API (${res.status})`;
    throw new ApiError(message, res.status, detail);
  }

  return res.json() as Promise<T>;
}

export const elevaApi = {
  health: () => request<HealthResponse>("/health"),
  analyze: (body: AnalyzeRequestBody) =>
    request<AnalyzeResponse>("/analyze", {
      method: "POST",
      body: JSON.stringify(body),
    }),
};
