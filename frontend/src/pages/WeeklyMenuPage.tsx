import type { WeeklyMenuResponse } from "../types/domain";
import { WEEK_DAY_LABELS_FR } from "../constants/weekdays";

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
            <span className="day-pill">{WEEK_DAY_LABELS_FR[item.day]}</span>
            <span>{item.dish?.name ?? "Pas encore de gagnant"}</span>
          </li>
        )) ?? <li className="empty">Aucun menu généré pour le moment.</li>}
      </ul>
    </section>
  );
}
