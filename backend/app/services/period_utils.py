"""Date and period calculation utilities for the meal planner.

This module handles all date-related logic for menu periods:
- Calculating current period (Thursday to Wednesday cycle)
- Determining if voting is open (Friday to Sunday)
- Checking if it's time to auto-finalize (Monday 23:59)
- Formatting period labels for display
"""

from datetime import datetime, timedelta


def get_current_period() -> dict:
    """
    Calculate the current menu period based on today's date.
    
    The menu cycle runs from Thursday to Wednesday (8 days):
    - Thursday, Friday, Saturday, Sunday, Monday, Tuesday, Wednesday, Thursday
    
    Returns:
        dict with:
        - start_date: ISO date string for the period's Thursday
        - end_date: ISO date string for the period's following Wednesday
        - period_id: start_date string (YYYY-MM-DD format)
        - display_label: Human-readable label (e.g., "16/04 - 23/04")
        - days: List of 8 dates from Thursday to Thursday
    """
    today = datetime.now()
    
    # Find the most recent Thursday (or today if it's Thursday)
    # Monday=0, Tuesday=1, Wednesday=2, Thursday=3, ...
    days_since_thursday = (today.weekday() - 3) % 7
    thursday = today - timedelta(days=days_since_thursday)
    
    # Period runs from Thursday to the following Wednesday
    start_date = thursday.replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = start_date + timedelta(days=7)  # Next Wednesday
    
    # The menu actually covers 8 days: Thu, Fri, Sat, Sun, Mon, Tue, Wed, Thu
    # So we need to show dates for 8 days
    period_days = []
    for i in range(8):
        period_days.append(start_date + timedelta(days=i))
    
    return {
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "period_id": start_date.strftime("%Y-%m-%d"),
        "display_label": f"{start_date.strftime('%d/%m')} - {end_date.strftime('%d/%m')}",
        "days": [d.strftime("%Y-%m-%d") for d in period_days],
    }


def is_voting_open() -> bool:
    """
    Check if voting is currently open.
    
    Voting is open from Friday 00:00 to Sunday 23:59.
    This allows members to vote for the upcoming menu period.
    
    Returns:
        True if voting is open, False otherwise
    """
    today = datetime.now()
    weekday = today.weekday()  # Monday=0, ..., Friday=4, Saturday=5, Sunday=6
    
    # Voting open: Friday (4), Saturday (5), Sunday (6)
    return weekday in (4, 5, 6)


def is_finalization_time() -> bool:
    """
    Check if it's time to auto-finalize the menu.
    
    Auto-finalization happens on Monday at 23:59 (end of day).
    This gives admins the entire Monday to make last-minute changes.
    
    Returns:
        True if it's Monday 23:59 or later, False otherwise
    """
    now = datetime.now()
    
    # Monday = 0
    is_monday = now.weekday() == 0
    is_late_evening = now.hour >= 23 and now.minute >= 59
    
    return is_monday and is_late_evening


def should_create_new_period() -> bool:
    """
    Check if we should create a new menu period.
    
    New periods are created on Tuesday after finalization.
    This happens automatically after the previous period is finalized.
    
    Returns:
        True if it's Tuesday or later and no active period exists
    """
    now = datetime.now()
    
    # Tuesday = 1
    return now.weekday() >= 1


def get_weekday_label(weekday_name: str) -> str:
    """
    Get the French label for a weekday.
    
    Args:
        weekday_name: English weekday name (e.g., "monday", "thursday")
    
    Returns:
        French label (e.g., "Lundi", "Jeudi")
    """
    labels = {
        "monday": "Lundi",
        "tuesday": "Mardi",
        "wednesday": "Mercredi",
        "thursday": "Jeudi",
        "friday": "Vendredi",
        "saturday": "Samedi",
        "sunday": "Dimanche",
    }
    return labels.get(weekday_name, weekday_name)


def get_date_for_weekday(period_start: str, weekday_name: str, day_index: int) -> str:
    """
    Get the formatted date for a specific weekday within a period.
    
    Args:
        period_start: ISO date string of the period's start (Thursday)
        weekday_name: English weekday name
        day_index: Position in the 8-day cycle (0-7)
    
    Returns:
        Formatted date string (DD/MM)
    """
    start_date = datetime.strptime(period_start, "%Y-%m-%d")
    target_date = start_date + timedelta(days=day_index)
    
    return target_date.strftime("%d/%m")


def get_full_date_for_weekday(period_start: str, day_index: int) -> str:
    """
    Get the full date label for a day in the period.
    
    Args:
        period_start: ISO date string of the period's start (Thursday)
        day_index: Position in the 8-day cycle (0-7)
    
    Returns:
        Formatted date with weekday (e.g., "Jeudi 16/04")
    """
    start_date = datetime.strptime(period_start, "%Y-%m-%d")
    target_date = start_date + timedelta(days=day_index)
    
    weekday_labels = {
        0: "Lundi",
        1: "Mardi",
        2: "Mercredi",
        3: "Jeudi",
        4: "Vendredi",
        5: "Samedi",
        6: "Dimanche",
    }
    
    weekday_label = weekday_labels[target_date.weekday()]
    date_label = target_date.strftime("%d/%m")
    
    return f"{weekday_label} {date_label}"


def get_period_from_date(date_str: str) -> dict:
    """
    Calculate which period a given date belongs to.
    
    Args:
        date_str: ISO date string (YYYY-MM-DD)
    
    Returns:
        Period dict for the period containing that date
    """
    target_date = datetime.strptime(date_str, "%Y-%m-%d")
    
    # Find the Thursday before (or on) this date
    days_since_thursday = (target_date.weekday() - 3) % 7
    thursday = target_date - timedelta(days=days_since_thursday)
    
    start_date = thursday.replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = start_date + timedelta(days=7)
    
    return {
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "period_id": start_date.strftime("%Y-%m-%d"),
        "display_label": f"{start_date.strftime('%d/%m')} - {end_date.strftime('%d/%m')}",
    }
