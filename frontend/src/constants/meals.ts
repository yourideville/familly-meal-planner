import type { Meal } from "../types/domain";

export const MEALS: Meal[] = ["lunch", "dinner"];

export const MEAL_LABELS_FR: Record<Meal, string> = {
  lunch: "Déjeuner",
  dinner: "Dîner",
};
