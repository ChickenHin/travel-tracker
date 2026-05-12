import type {
  ParseReceiptResp,
  ReviewReq,
  ReviewResp,
  SummaryResp,
  SummaryFiltersQuery,
} from "../types";

const BASE_URL = import.meta.env.VITE_API_BASE_URL;
const API_KEY = import.meta.env.VITE_API_KEY;

if (!BASE_URL || !API_KEY) {
  console.error("Missing VITE_API_BASE_URL or VITE_API_KEY in .env.local");
}

async function requestWithApimSecret<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: {
      "Ocp-Apim-Subscription-Key": API_KEY,
      ...(options.headers || {}),
    },
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(`HTTP ${response.status}: ${text || response.statusText}`);
  }

  return response.json() as Promise<T>;
}

export async function parseReceipt(file: File): Promise<ParseReceiptResp> {
  return requestWithApimSecret<ParseReceiptResp>("/receipts/parse", {
    method: "POST",
    headers: { "Content-Type": "application/octet-stream" },
    body: file,
  });
}

export async function saveReview(review: ReviewReq): Promise<ReviewResp> {
  return requestWithApimSecret<ReviewResp>("/reviews", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(review),
  });
}

export async function getSummary(
  filters: SummaryFiltersQuery = {},
): Promise<SummaryResp> {
  const params = new URLSearchParams();
  if (filters.city) params.append("city", filters.city);
  if (filters.country) params.append("country", filters.country);
  if (filters.from) params.append("from", filters.from);
  if (filters.to) params.append("to", filters.to);

  const query = params.toString() ? `?${params}` : "";
  return requestWithApimSecret<SummaryResp>(`/reviews/summary${query}`);
}
