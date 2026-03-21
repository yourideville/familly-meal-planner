import type { WeeklyMenuResponse } from "../types/domain";

interface WeeklyMenuPageProps {
  menu: WeeklyMenuResponse | null;
  onRefresh: () => Promise<void>;
}

export function WeeklyMenuPage({ menu, onRefresh }: WeeklyMenuPageProps) {
  return (
    <section>
      <h2>Weekly Menu</h2>
      <button onClick={() => void onRefresh()} type="button">
        Refresh menu
      </button>
      <ul>
        {menu?.items.map((item) => (
          <li key={item.day}>
            <strong>{item.day}:</strong> {item.dish?.name ?? "No winner yet"}
          </li>
        )) ?? <li>No menu generated yet.</li>}
      </ul>
    </section>
  );
}
