import type { Dish, Vote, VotePayload, WeeklyMenuResponse } from "../types/domain";

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

export function getVotes(): Promise<Vote[]> {
  return request<Vote[]>("/votes");
}

export function getWeeklyMenu(): Promise<WeeklyMenuResponse> {
  return request<WeeklyMenuResponse>("/weekly-menu");
}

export function createDish(payload: Omit<Dish, "id">): Promise<Dish> {
  return request<Dish>("/admin/dishes", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateDish(id: string, payload: Omit<Dish, "id">): Promise<Dish> {
  return request<Dish>(`/admin/dishes/${id}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export function deleteDish(id: string): Promise<void> {
  return request<void>(`/admin/dishes/${id}`, {
    method: "DELETE",
  });
}

export function setMenuItem(day: string, dishId: string | null): Promise<WeeklyMenuResponse> {
  return request<WeeklyMenuResponse>(`/admin/menu/item/${day}`, {
    method: "PUT",
    body: JSON.stringify({ dish_id: dishId }),
  });
}

export function setShortlist(day: string, dishIds: string[]): Promise<WeeklyMenuResponse> {
  return request<WeeklyMenuResponse>(`/admin/menu/shortlist/${day}`, {
    method: "PUT",
    body: JSON.stringify(dishIds),
  });
}

export function validateWeeklyMenu(): Promise<WeeklyMenuResponse> {
  return request<WeeklyMenuResponse>("/admin/menu/validate", {
    method: "POST",
  });
}

export function unvalidateWeeklyMenu(): Promise<WeeklyMenuResponse> {
  return request<WeeklyMenuResponse>("/admin/menu/validate", {
    method: "DELETE",
  });
}
