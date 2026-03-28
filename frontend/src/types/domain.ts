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
  items: WeeklyMenuItem[];
  finalized?: boolean;
  shortlists?: Partial<Record<Weekday, Partial<Record<Meal, string[]>>>>;
}
