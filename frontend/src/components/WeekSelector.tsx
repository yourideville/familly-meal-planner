import type { MenuPeriod } from "../types/domain";

interface WeekSelectorProps {
  periods: MenuPeriod[];
  selectedPeriod: string | null;  // null = current week
  onSelect: (periodId: string | null) => void;
}

export function WeekSelector({ periods, selectedPeriod, onSelect }: WeekSelectorProps) {
  return (
    <div className="week-selector">
      <label htmlFor="week-select" className="week-selector-label">
        Semaine
      </label>
      <select
        id="week-select"
        value={selectedPeriod ?? "current"}
        onChange={(e) => onSelect(e.target.value === "current" ? null : e.target.value)}
        className="week-select-input"
      >
        <option value="current">Menu de la semaine</option>
        {periods.map((period) => (
          <option key={period.period_id} value={period.period_id}>
            {period.display_label}
            {period.finalized_at ? " ✓" : ""}
          </option>
        ))}
      </select>
    </div>
  );
}
