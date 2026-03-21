import type { Dish, VotePayload, WeeklyMenuResponse } from "../types/domain";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
    },
    ...options,
  });

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export function getDishes(): Promise<Dish[]> {
  return request<Dish[]>("/dishes");
}

export function createVote(payload: VotePayload): Promise<VotePayload> {
  return request<VotePayload>("/votes", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getWeeklyMenu(): Promise<WeeklyMenuResponse> {
  return request<WeeklyMenuResponse>("/weekly-menu");
}
