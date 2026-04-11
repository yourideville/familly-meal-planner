import type { MenuPeriod } from "../types/domain";
import { WEEK_SELECTOR_LABELS, FINALIZED_INDICATOR } from "../constants/week-selector";

interface WeekSelectorProps {
  periods: MenuPeriod[];
  selectedPeriod: string | null;  // null = current week
  onSelect: (periodId: string | null) => void;
}

export function WeekSelector({ periods, selectedPeriod, onSelect }: WeekSelectorProps) {
  return (
    <div className="week-selector">
      <label htmlFor="week-select" className="week-selector-label">
        {WEEK_SELECTOR_LABELS.label}
      </label>
      <select
        id="week-select"
        value={selectedPeriod ?? "current"}
        onChange={(e) => onSelect(e.target.value === "current" ? null : e.target.value)}
        className="week-select-input"
      >
        <option value="current">{WEEK_SELECTOR_LABELS.currentWeek}</option>
        {periods.map((period) => (
          <option key={period.period_id} value={period.period_id}>
            {period.display_label}
            {period.finalized_at ? FINALIZED_INDICATOR : ""}
          </option>
        ))}
      </select>
    </div>
  );
}
