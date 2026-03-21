import type { WeeklyMenuResponse } from "../types/domain";
import type { Weekday } from "../types/domain";

const weekDayLabels: Record<Weekday, string> = {
  monday: "Lundi",
  tuesday: "Mardi",
  wednesday: "Mercredi",
  thursday: "Jeudi",
  friday: "Vendredi",
  saturday: "Samedi",
  sunday: "Dimanche",
};

interface WeeklyMenuPageProps {
  menu: WeeklyMenuResponse | null;
  onRefresh: () => Promise<void>;
}

export function WeeklyMenuPage({ menu, onRefresh }: WeeklyMenuPageProps) {
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
      <ul className="menu-list">
        {menu?.items.map((item) => (
          <li key={item.day} className="menu-item">
            <span className="day-pill">{weekDayLabels[item.day]}</span>
            <span>{item.dish?.name ?? "Pas encore de gagnant"}</span>
          </li>
        )) ?? <li className="empty">Aucun menu généré pour le moment.</li>}
      </ul>
    </section>
  );
}
