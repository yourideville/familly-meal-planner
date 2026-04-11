/**
 * Date utilities for the weekly menu page.
 *
 * All date parsing is done in local timezone to avoid UTC shift issues.
 */

/**
 * Calculate the date label for a specific day index within a period.
 *
 * @param periodStart - ISO date string (YYYY-MM-DD) of the period's start
 * @param dayIndex - Position in the period (0-7)
 * @returns Formatted date string (DD/MM) in local timezone
 */
export function getDateForDay(periodStart: string, dayIndex: number): string {
  // Parse ISO date in local timezone to avoid UTC midnight shift
  const [year, month, day] = periodStart.split("-").map(Number);
  const start = new Date(year, month - 1, day); // month is 0-indexed in JS
  const targetDate = new Date(start);
  targetDate.setDate(start.getDate() + dayIndex);

  const targetDay = String(targetDate.getDate()).padStart(2, "0");
  const targetMonth = String(targetDate.getMonth() + 1).padStart(2, "0");
  return `${targetDay}/${targetMonth}`;
}
