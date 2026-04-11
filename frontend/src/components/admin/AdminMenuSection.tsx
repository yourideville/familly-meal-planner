import { useMemo } from "react";
import { AdminButton } from "./AdminButton";
import { AdminSection } from "./AdminSection";
import { MEAL_LABELS_FR, MEALS } from "../../constants/meals";
import { WEEK_DAY_LABELS_FR, WEEK_DAYS } from "../../constants/weekdays";
import type { Dish, Meal, Vote, WeeklyMenuResponse, Weekday } from "../../types/domain";

interface AdminMenuSectionProps {
  dishes: Dish[];
  votes: Vote[];
  selectedDay: Weekday;
  selectedMeal: Meal;
  selectedManualDish: string;
  onSelectDay: (value: Weekday) => void;
  onSelectMeal: (value: Meal) => void;
  onSelectManualDish: (value: string) => void;
  onSetManualMenu: () => void;
  onValidateMenu: () => void;
  onUnvalidateMenu: () => void;
  menu: WeeklyMenuResponse | null;
}

export function AdminMenuSection({
  dishes,
  votes,
  selectedDay,
  selectedMeal,
  selectedManualDish,
  onSelectDay,
  onSelectMeal,
  onSelectManualDish,
  onSetManualMenu,
  onValidateMenu,
  onUnvalidateMenu,
  menu,
}: AdminMenuSectionProps) {
  const filteredDishes = useMemo(
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

  const votesForSlot = useMemo(
    () =>
      votes
        .filter((vote) => vote.day === selectedDay && vote.meal === selectedMeal)
        .map((vote) => ({
          ...vote,
          dishName: dishes.find((d) => d.id === vote.dish_id)?.name ?? vote.dish_id,
        })),
    [votes, selectedDay, selectedMeal, dishes],
  );

  const voteCounts = useMemo(() => {
    const counts: Record<string, string[]> = {};
    votesForSlot.forEach((vote) => {
      if (!counts[vote.dish_id]) {
        counts[vote.dish_id] = [];
      }
      counts[vote.dish_id].push(vote.user_name);
    });
    return counts;
  }, [votesForSlot]);

  return (
    <div className="admin-body">
      <AdminSection title="Remplacement manuel" description="Forcer un plat spécifique pour un jour et un repas.">
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
          <label>
            Plat manuel
            <select value={selectedManualDish} onChange={(event) => onSelectManualDish(event.target.value)}>
              <option value="">Utiliser les votes</option>
              {filteredDishes.map((dish) => (
                <option key={dish.id} value={dish.id}>
                  {dish.name}
                </option>
              ))}
            </select>
          </label>
        </div>

        <AdminButton onClick={onSetManualMenu} type="button">
          Enregistrer le remplacement
        </AdminButton>
      </AdminSection>

      <AdminSection title="Votes pour ce créneau" description={`Votes pour ${WEEK_DAY_LABELS_FR[selectedDay]} ${MEAL_LABELS_FR[selectedMeal]}.`}>
        {Object.keys(voteCounts).length === 0 ? (
          <p className="status-text">Aucun vote pour ce créneau.</p>
        ) : (
          <ul className="vote-list">
            {Object.entries(voteCounts)
              .sort(([, aVoters], [, bVoters]) => bVoters.length - aVoters.length)
              .map(([dishId, voters]) => {
                const dish = dishes.find((d) => d.id === dishId);
                return (
                  <li key={dishId}>
                    <span className="vote-dish-name">{dish?.name ?? dishId}</span>
                    <span className="vote-count">{voters.length} vote{voters.length > 1 ? "s" : ""}</span>
                    <span className="vote-voters">{voters.join(", ")}</span>
                  </li>
                );
              })}
          </ul>
        )}
      </AdminSection>

      <AdminSection title="Validation finale" description="Valider ou dévalider le menu de la semaine.">
        <div className="button-pair">
          <AdminButton onClick={onValidateMenu} type="button" disabled={menu?.finalized}>
            Valider le menu
          </AdminButton>
          <AdminButton onClick={onUnvalidateMenu} type="button" disabled={!menu?.finalized} danger>
            Dévalider le menu
          </AdminButton>
        </div>
        <p className="status-text">État finalisé : {menu?.finalized ? "oui" : "non"}</p>
      </AdminSection>
    </div>
  );
}
