import { useEffect, useState } from "react";
import type { MenuPeriod, Weekday, WeeklyMenuResponse } from "../types/domain";
import { WEEK_DAY_LABELS_FR, WEEK_DAYS } from "../constants/weekdays";
import { MEAL_LABELS_FR, MEALS } from "../constants/meals";
import { WeekSelector } from "../components/WeekSelector";
import { getMenuPeriods } from "../api/client";

interface WeeklyMenuPageProps {
  menu: WeeklyMenuResponse | null;
  onRefresh: () => Promise<void>;
}

function getDateForDay(periodStart: string, dayIndex: number): string {
  const start = new Date(periodStart);
  const targetDate = new Date(start);
  targetDate.setDate(start.getDate() + dayIndex);
  
  const day = String(targetDate.getDate()).padStart(2, '0');
  const month = String(targetDate.getMonth() + 1).padStart(2, '0');
  return `${day}/${month}`;
}

export function WeeklyMenuPage({ menu, onRefresh }: WeeklyMenuPageProps) {
  const [periods, setPeriods] = useState<MenuPeriod[]>([]);
  const [selectedPeriod, setSelectedPeriod] = useState<string | null>(null);
  const [loadingPeriod, setLoadingPeriod] = useState(false);

  useEffect(() => {
    void loadPeriods();
  }, []);

  async function loadPeriods() {
    try {
      const periodList = await getMenuPeriods();
      setPeriods(periodList);
    } catch (error) {
      console.error("Failed to load periods:", error);
    }
  }

  async function handlePeriodSelect(periodId: string | null) {
    setSelectedPeriod(periodId);
    if (periodId) {
      setLoadingPeriod(true);
      try {
        // Fetch specific period's menu (would need backend endpoint for this)
        // For now, just refresh current menu
        await onRefresh();
      } finally {
        setLoadingPeriod(false);
      }
    } else {
      await onRefresh();
    }
  }

  const itemsByDay = menu?.items.reduce<Record<string, Record<string, string>>>(
    (acc, item) => {
      const dayGroup = acc[item.day] ?? { lunch: "Pas encore de gagnant", dinner: "Pas encore de gagnant" };
      dayGroup[item.meal] = item.dish?.name ?? "Pas encore de gagnant";
      acc[item.day] = dayGroup;
      return acc;
    },
    {},
  );

  // Map weekdays to their position in the 8-day cycle (Thu-Thu)
  const weekdayOrder: Weekday[] = [
    "thursday", "friday", "saturday", "sunday", 
    "monday", "tuesday", "wednesday", "thursday"
  ];
  
  const periodStart = menu?.start_date;
  const periodLabel = menu?.period_label ?? "";

  return (
    <section className="card">
      <div className="section-head section-head-row">
        <div>
          <h2>Menu hebdomadaire</h2>
          {periodLabel && (
            <p className="period-label">Menu du {periodLabel}</p>
          )}
          <p>Visualisez les plats retenus pour chaque jour.</p>
        </div>
        <div className="menu-actions">
          <WeekSelector
            periods={periods}
            selectedPeriod={selectedPeriod}
            onSelect={handlePeriodSelect}
          />
          <button 
            onClick={() => void onRefresh()} 
            type="button"
            disabled={loadingPeriod}
          >
            {loadingPeriod ? "Chargement..." : "Actualiser le menu"}
          </button>
        </div>
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
          {WEEK_DAYS.map((day, index) => {
            // Calculate actual date for this day in the period
            const dayIndex = weekdayOrder.indexOf(day as any);
            const dateLabel = periodStart && dayIndex >= 0 
              ? getDateForDay(periodStart, dayIndex)
              : null;
            
            return (
              <tr key={day}>
                <td>
                  <span className="weekday-name">{WEEK_DAY_LABELS_FR[day]}</span>
                  {dateLabel && <span className="weekday-date"> ({dateLabel})</span>}
                </td>
                {MEALS.map((meal) => (
                  <td key={meal}>{itemsByDay?.[day]?.[meal] ?? "Pas encore de gagnant"}</td>
                ))}
              </tr>
            );
          })}
        </tbody>
      </table>
    </section>
  );
}
