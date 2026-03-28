import type { WeeklyMenuResponse } from "../types/domain";
import { WEEK_DAY_LABELS_FR } from "../constants/weekdays";
import { MEAL_LABELS_FR, MEALS } from "../constants/meals";

interface WeeklyMenuPageProps {
  menu: WeeklyMenuResponse | null;
  onRefresh: () => Promise<void>;
}

export function WeeklyMenuPage({ menu, onRefresh }: WeeklyMenuPageProps) {
  const itemsByDay = menu?.items.reduce<Record<string, Record<string, string>>>(
    (acc, item) => {
      const dayGroup = acc[item.day] ?? { lunch: "Pas encore de gagnant", dinner: "Pas encore de gagnant" };
      dayGroup[item.meal] = item.dish?.name ?? "Pas encore de gagnant";
      acc[item.day] = dayGroup;
      return acc;
    },
    {},
  );

  return (
    <section className="card">
      <div className="section-head section-head-row">
        <div>
          <h2>Menu hebdomadaire</h2>
          <p>Visualisez les plats retenus pour chaque jour.</p>
        </div>
        <button onClick={() => void onRefresh()} type="button">
          Actualiser le menu
        </button>
      </div>
      <table className="weekly-menu-table">
        <thead>
          <tr>
            <th>Jour</th>
            {MEALS.map((meal) => (
              <th key={meal}>{MEAL_LABELS_FR[meal]}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {Object.keys(itemsByDay ?? {}).map((day) => (
            <tr key={day}>
              <td>{WEEK_DAY_LABELS_FR[day as keyof typeof WEEK_DAY_LABELS_FR]}</td>
              {MEALS.map((meal) => (
                <td key={meal}>{itemsByDay?.[day]?.[meal] ?? "Pas encore de gagnant"}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
