import { useEffect, useState } from "react";
import type { MenuPeriod, Weekday, WeeklyMenuResponse } from "../types/domain";
import { WEEK_DAY_LABELS_FR } from "../constants/weekdays";
import { MEAL_LABELS_FR, MEALS } from "../constants/meals";
import { WEEKLY_MENU_LABELS } from "../constants/weekly-menu";
import { WeekSelector } from "../components/WeekSelector";
import { getMenuPeriods } from "../api/client";
import { getDateForDay } from "../utils/date";

/** Days in the menu period order: Thursday to Wednesday */
const MENU_DAYS: Weekday[] = [
  "thursday",
  "friday",
  "saturday",
  "sunday",
  "monday",
  "tuesday",
  "wednesday",
];

interface WeeklyMenuPageProps {
  menu: WeeklyMenuResponse | null;
  onRefresh: () => Promise<void>;
}

export function WeeklyMenuPage({ menu, onRefresh }: WeeklyMenuPageProps) {
  const [periods, setPeriods] = useState<MenuPeriod[]>([]);
  const [selectedPeriod, setSelectedPeriod] = useState<string | null>(null);
  const [loadingPeriod, setLoadingPeriod] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    void loadPeriods();
  }, []);

  async function loadPeriods() {
    try {
      setLoadError(null);
      const periodList = await getMenuPeriods();
      setPeriods(periodList);
    } catch (error) {
      console.error("Failed to load periods:", error);
      setLoadError("Impossible de charger les périodes.");
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

  const itemsByDay = menu?.items.reduce<Record<Weekday, Record<string, string>>>(
    (acc, item) => {
      const dayGroup = acc[item.day] ?? { lunch: WEEKLY_MENU_LABELS.noWinner, dinner: WEEKLY_MENU_LABELS.noWinner };
      dayGroup[item.meal] = item.dish?.name ?? WEEKLY_MENU_LABELS.noWinner;
      acc[item.day] = dayGroup;
      return acc;
    },
    {} as Record<Weekday, Record<string, string>>,
  );

  const periodStart = menu?.start_date;
  const periodLabel = menu?.period_label ?? "";

  return (
    <section className="card">
      <div className="section-head section-head-row">
        <div>
          <h2>{WEEKLY_MENU_LABELS.title}</h2>
          {periodLabel && (
            <p className="period-label">{WEEKLY_MENU_LABELS.menuOf} {periodLabel}</p>
          )}
          <p>{WEEKLY_MENU_LABELS.description}</p>
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
            {loadingPeriod ? WEEKLY_MENU_LABELS.loading : WEEKLY_MENU_LABELS.refresh}
          </button>
        </div>
      </div>

      {loadError && (
        <div className="error-message" role="alert">
          {loadError}
        </div>
      )}

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
          {MENU_DAYS.map((day, index) => {
            const dateLabel = periodStart
              ? getDateForDay(periodStart, index)
              : null;

            return (
              <tr key={day}>
                <td>
                  <span className="weekday-name">{WEEK_DAY_LABELS_FR[day]}</span>
                  {dateLabel && <span className="weekday-date"> ({dateLabel})</span>}
                </td>
                {MEALS.map((meal) => (
                  <td key={meal}>{itemsByDay?.[day]?.[meal] ?? WEEKLY_MENU_LABELS.noWinner}</td>
                ))}
              </tr>
            );
          })}
        </tbody>
      </table>
    </section>
  );
}
