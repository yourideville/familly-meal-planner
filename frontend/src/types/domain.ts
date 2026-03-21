export type Weekday =
  | "monday"
  | "tuesday"
  | "wednesday"
  | "thursday"
  | "friday"
  | "saturday"
  | "sunday";

export interface Dish {
  id: string;
  name: string;
  tags: string[];
}

export interface VotePayload {
  user_name: string;
  dish_id: string;
  day: Weekday;
}

export interface WeeklyMenuItem {
  day: Weekday;
  dish: Dish | null;
}

export interface WeeklyMenuResponse {
  items: WeeklyMenuItem[];
}
