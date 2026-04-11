export type Weekday =
  | "monday"
  | "tuesday"
  | "wednesday"
  | "thursday"
  | "friday"
  | "saturday"
  | "sunday";

export type Meal = "lunch" | "dinner";

export type DishCategory =
  | "lunch"
  | "dinner"
  | "weekends_lunch"
  | "saturday_dinner";

export interface Dish {
  id: string;
  name: string;
  tags: string[];
  category: DishCategory;
}

export interface FamilyMember {
  name: string;
}

export interface Vote {
  user_name: string;
  dish_id: string;
  day: Weekday;
  meal: Meal;
}

export interface VotePayload {
  user_name: string;
  dish_id: string;
  day: Weekday;
  meal: Meal;
}

export interface WeeklyMenuItem {
  day: Weekday;
  meal: Meal;
  dish: Dish | null;
}

export interface VoteSlot {
  day: Weekday;
  meal: Meal;
  available: boolean;
}

export interface WeeklyMenuResponse {
  period_id: string;  // e.g., "2026-04-16"
  period_label: string;  // e.g., "16/04 - 23/04"
  start_date: string;  // ISO date (Thursday)
  end_date: string;  // ISO date (following Wednesday)
  items: WeeklyMenuItem[];
  finalized?: boolean;
  shortlists?: Partial<Record<Weekday, Partial<Record<Meal, string[]>>>>;
}

export interface MenuPeriod {
  period_id: string;  // e.g., "2026-04-16"
  start_date: string;  // ISO date (Thursday)
  end_date: string;  // ISO date (following Wednesday)
  display_label: string;  // e.g., "16/04 - 23/04"
  created_at: string;  // ISO timestamp
  finalized_at: string | null;  // ISO timestamp or null
}

export type AvailabilityMap = Record<Weekday, Record<Meal, boolean>>;

export interface AdminLoginPayload {
  username: string;
  password: string;
}

export interface AdminSessionResponse {
  authenticated: boolean;
}
