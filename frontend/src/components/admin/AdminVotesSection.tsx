import { useMemo } from "react";
import { AdminButton } from "./AdminButton";
import { AdminSection } from "./AdminSection";
import { MEAL_LABELS_FR, MEALS } from "../../constants/meals";
import { WEEK_DAY_LABELS_FR, WEEK_DAYS } from "../../constants/weekdays";
import type { Dish, Meal, Weekday } from "../../types/domain";

interface AdminVotesSectionProps {
  dishes: Dish[];
  availability: Record<Weekday, Record<Meal, boolean>>;
  selectedDay: Weekday;
  selectedMeal: Meal;
  selectedShortlist: string[];
  onSelectDay: (value: Weekday) => void;
  onSelectMeal: (value: Meal) => void;
  onToggleAvailability: (day: Weekday, meal: Meal) => void;
  onToggleShortlist: (dishId: string, selected: boolean) => void;
  onSetShortlist: () => void;
  shortlist: string[];
}

export function AdminVotesSection({
  dishes,
  availability,
  selectedDay,
  selectedMeal,
  selectedShortlist,
  onSelectDay,
  onSelectMeal,
  onToggleAvailability,
  onToggleShortlist,
  onSetShortlist,
  shortlist,
}: AdminVotesSectionProps) {
  const sortedDishes = useMemo(
    () =>
      [...dishes]
        .filter((dish) => {
          if (selectedDay === "saturday") {
            if (selectedMeal === "lunch") return dish.category === "weekends_lunch";
            return selectedMeal === "dinner" && dish.category === "saturday_dinner";
          }
          if (selectedDay === "sunday") {
            if (selectedMeal === "lunch") return dish.category === "weekends_lunch";
            return selectedMeal === "dinner" && dish.category === "dinner";
          }
          return dish.category === selectedMeal;
        })
        .sort((a, b) => a.name.localeCompare(b.name)),
    [dishes, selectedDay, selectedMeal],
  );

  return (
    <div className="admin-body">
      <AdminSection title="Disponibilité des votes" description="Activer ou désactiver les créneaux par jour et repas.">
        <table className="availability-table">
          <thead>
            <tr>
              <th>Jour</th>
              {MEALS.map((meal) => (
                <th key={meal}>{MEAL_LABELS_FR[meal]}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {WEEK_DAYS.map((day) => (
              <tr key={day}>
                <td>{WEEK_DAY_LABELS_FR[day]}</td>
                {MEALS.map((meal) => (
                  <td key={meal}>
                    <AdminButton onClick={() => onToggleAvailability(day, meal)} type="button">
                      {availability[day][meal] ? "Ouvert" : "Fermé"}
                    </AdminButton>
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </AdminSection>

      <AdminSection title="Shortlist" description="Sélectionner les plats candidats pour un repas précis.">
        <div className="form-grid">
          <label>
            Jour
            <select value={selectedDay} onChange={(event) => onSelectDay(event.target.value as Weekday)}>
              {WEEK_DAYS.map((day) => (
                <option key={day} value={day}>
                  {WEEK_DAY_LABELS_FR[day]}
                </option>
              ))}
            </select>
          </label>
          <label>
            Repas
            <select value={selectedMeal} onChange={(event) => onSelectMeal(event.target.value as Meal)}>
              {MEALS.map((meal) => (
                <option key={meal} value={meal}>
                  {MEAL_LABELS_FR[meal]}
                </option>
              ))}
            </select>
          </label>
        </div>

        <div className="shortlist-grid">
          {sortedDishes.map((dish) => (
            <label key={dish.id}>
              <input
                type="checkbox"
                checked={selectedShortlist.includes(dish.id)}
                onChange={(event) => onToggleShortlist(dish.id, event.target.checked)}
              />
              {dish.name}
            </label>
          ))}
        </div>

        <AdminButton onClick={onSetShortlist} type="button">
          Enregistrer shortlist
        </AdminButton>

        <p className="status-text">
          Shortlist actuelle pour {WEEK_DAY_LABELS_FR[selectedDay]} {MEAL_LABELS_FR[selectedMeal]} : {shortlist
            .map((id) => dishes.find((dish) => dish.id === id)?.name)
            .filter(Boolean)
            .join(", ") || "(vide)"}
        </p>
      </AdminSection>
    </div>
  );
}
