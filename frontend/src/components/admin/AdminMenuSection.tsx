import type { Dispatch, SetStateAction } from "react";
import { AdminButton } from "./AdminButton";
import { AdminSection } from "./AdminSection";
import { MEAL_LABELS_FR, MEALS } from "../../constants/meals";
import { WEEK_DAY_LABELS_FR, WEEK_DAYS } from "../../constants/weekdays";
import type { Dish, Meal, WeeklyMenuResponse, Weekday } from "../../types/domain";

interface AdminMenuSectionProps {
  dishes: Dish[];
  selectedDay: Weekday;
  selectedMeal: Meal;
  selectedManualDish: string;
  onSelectDay: Dispatch<SetStateAction<Weekday>>;
  onSelectMeal: Dispatch<SetStateAction<Meal>>;
  onSelectManualDish: Dispatch<SetStateAction<string>>;
  onSetManualMenu: () => void;
  onValidateMenu: () => void;
  onUnvalidateMenu: () => void;
  menu: WeeklyMenuResponse | null;
}

export function AdminMenuSection({
  dishes,
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
              {dishes.map((dish) => (
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
