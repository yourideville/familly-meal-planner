import type {
  AdminLoginPayload,
  AdminSessionResponse,
  Dish,
  FamilyMember,
  Meal,
  Vote,
  VotePayload,
  WeeklyMenuResponse,
  VoteSlot,
  DishCategory,
} from "../types/domain";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
    },
    ...options,
  });

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }

  if (response.status === 204) {
    return undefined as unknown as T;
  }

  return response.json() as Promise<T>;
}

export function getDishes(): Promise<Dish[]> {
  return request<Dish[]>("/dishes");
}

export function getMembers(): Promise<string[]> {
  return request<string[]>("/members");
}

export function createMember(payload: FamilyMember): Promise<string> {
  return request<string>("/admin/members", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateMember(name: string, payload: FamilyMember): Promise<string> {
  return request<string>(`/admin/members/${encodeURIComponent(name)}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export function deleteMember(name: string): Promise<void> {
  return request<void>(`/admin/members/${encodeURIComponent(name)}`, {
    method: "DELETE",
  });
}

export function getVoteAvailability(): Promise<VoteSlot[]> {
  return request<VoteSlot[]>("/admin/vote-availability");
}

export function setVoteAvailability(slots: VoteSlot[]): Promise<VoteSlot[]> {
  return request<VoteSlot[]>("/admin/vote-availability", {
    method: "PUT",
    body: JSON.stringify(slots),
  });
}

export function getDishCategories(): Promise<DishCategory[]> {
  return request<DishCategory[]>("/admin/dishes/categories");
}

export function loginAdmin(payload: AdminLoginPayload): Promise<AdminSessionResponse> {
  return request<AdminSessionResponse>("/admin/login", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function logoutAdmin(): Promise<AdminSessionResponse> {
  return request<AdminSessionResponse>("/admin/logout", {
    method: "POST",
  });
}

export function checkAdminSession(): Promise<AdminSessionResponse> {
  return request<AdminSessionResponse>("/admin/session");
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

export function setMenuItem(day: string, meal: Meal, dishId: string | null): Promise<WeeklyMenuResponse> {
  return request<WeeklyMenuResponse>("/admin/menu/item", {
    method: "PUT",
    body: JSON.stringify({ day, meal, dish_id: dishId }),
  });
}

export function setShortlist(day: string, meal: Meal, dishIds: string[]): Promise<WeeklyMenuResponse> {
  return request<WeeklyMenuResponse>("/admin/menu/shortlist", {
    method: "PUT",
    body: JSON.stringify([{ day, meal, dish_ids: dishIds }]),
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
