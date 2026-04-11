"""Tests for period_utils module.

Covers date/period calculations, voting windows, and date formatting utilities.
"""

from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from app.services.period_utils import (
    get_current_period,
    get_date_for_weekday,
    get_full_date_for_weekday,
    get_period_from_date,
    get_weekday_label,
    is_finalization_time,
    is_voting_open,
    should_create_new_period,
)


class TestGetCurrentPeriod:
    """Test get_current_period function."""

    def test_returns_period_for_thursday(self):
        """When today is Thursday, period starts today."""
        # 2026-04-16 is a Thursday
        with patch("app.services.period_utils.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(2026, 4, 16)
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)

            result = get_current_period()

            assert result["start_date"] == "2026-04-16"
            assert result["end_date"] == "2026-04-23"  # Next Wednesday
            assert result["period_id"] == "2026-04-16"
            assert result["display_label"] == "16/04 - 23/04"
            assert len(result["days"]) == 8
            assert result["days"][0] == "2026-04-16"  # Thursday
            assert result["days"][7] == "2026-04-23"  # Following Thursday

    def test_returns_period_for_friday(self):
        """When today is Friday, period started on previous Thursday."""
        # 2026-04-17 is a Friday
        with patch("app.services.period_utils.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(2026, 4, 17)
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)

            result = get_current_period()

            assert result["start_date"] == "2026-04-16"
            assert result["end_date"] == "2026-04-23"

    def test_returns_period_for_wednesday(self):
        """When today is Wednesday, period started on previous Thursday."""
        # 2026-04-22 is a Wednesday
        with patch("app.services.period_utils.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(2026, 4, 22)
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)

            result = get_current_period()

            assert result["start_date"] == "2026-04-16"
            assert result["end_date"] == "2026-04-23"

    def test_days_cover_eight_days(self):
        """Period should cover 8 days from Thursday to following Thursday."""
        with patch("app.services.period_utils.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(2026, 4, 16)
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)

            result = get_current_period()

            assert len(result["days"]) == 8
            # Should be Thu, Fri, Sat, Sun, Mon, Tue, Wed, Thu
            expected = [
                "2026-04-16", "2026-04-17", "2026-04-18", "2026-04-19",
                "2026-04-20", "2026-04-21", "2026-04-22", "2026-04-23"
            ]
            assert result["days"] == expected


class TestIsVotingOpen:
    """Test is_voting_open function."""

    @pytest.mark.parametrize("date,expected", [
        (datetime(2026, 4, 17), True),   # Friday
        (datetime(2026, 4, 18), True),   # Saturday
        (datetime(2026, 4, 19), True),   # Sunday
        (datetime(2026, 4, 16), False),  # Thursday
        (datetime(2026, 4, 20), False),  # Monday
        (datetime(2026, 4, 21), False),  # Tuesday
        (datetime(2026, 4, 22), False),  # Wednesday
    ])
    def test_voting_open_on_correct_days(self, date, expected):
        with patch("app.services.period_utils.datetime") as mock_datetime:
            mock_datetime.now.return_value = date
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)

            result = is_voting_open()
            assert result == expected


class TestIsFinalizationTime:
    """Test is_finalization_time function."""

    def test_returns_true_on_monday_2359(self):
        """Should return True on Monday at 23:59."""
        # 2026-04-20 is a Monday
        with patch("app.services.period_utils.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(2026, 4, 20, 23, 59)
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)

            assert is_finalization_time() is True

    def test_returns_true_on_monday_after_2359(self):
        """Should return True on Monday after 23:59."""
        with patch("app.services.period_utils.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(2026, 4, 20, 23, 59, 30)
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)

            assert is_finalization_time() is True

    def test_returns_false_on_monday_before_2359(self):
        """Should return False on Monday before 23:59."""
        with patch("app.services.period_utils.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(2026, 4, 20, 22, 0)
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)

            assert is_finalization_time() is False

    def test_returns_false_on_tuesday(self):
        """Should return False on Tuesday."""
        # 2026-04-21 is a Tuesday
        with patch("app.services.period_utils.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(2026, 4, 21, 23, 59)
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)

            assert is_finalization_time() is False


class TestShouldCreateNewPeriod:
    """Test should_create_new_period function."""

    @pytest.mark.parametrize("date,expected", [
        (datetime(2026, 4, 21), True),   # Tuesday
        (datetime(2026, 4, 22), True),   # Wednesday
        (datetime(2026, 4, 16), True),   # Thursday
        (datetime(2026, 4, 17), True),   # Friday
        (datetime(2026, 4, 18), True),   # Saturday
        (datetime(2026, 4, 19), True),   # Sunday
        (datetime(2026, 4, 20), False),  # Monday
    ])
    def test_should_create_new_period(self, date, expected):
        with patch("app.services.period_utils.datetime") as mock_datetime:
            mock_datetime.now.return_value = date
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)

            result = should_create_new_period()
            assert result == expected


class TestGetWeekdayLabel:
    """Test get_weekday_label function."""

    @pytest.mark.parametrize("weekday,expected", [
        ("monday", "Lundi"),
        ("tuesday", "Mardi"),
        ("wednesday", "Mercredi"),
        ("thursday", "Jeudi"),
        ("friday", "Vendredi"),
        ("saturday", "Samedi"),
        ("sunday", "Dimanche"),
    ])
    def test_get_weekday_label(self, weekday, expected):
        assert get_weekday_label(weekday) == expected

    def test_returns_unknown_for_invalid_weekday(self):
        assert get_weekday_label("invalid") == "invalid"


class TestGetDateForWeekday:
    """Test get_date_for_weekday function."""

    def test_returns_correct_date_for_day_index(self):
        """Should return formatted date for given day index."""
        result = get_date_for_weekday("2026-04-16", "thursday", 0)
        assert result == "16/04"

        result = get_date_for_weekday("2026-04-16", "friday", 1)
        assert result == "17/04"

        result = get_date_for_weekday("2026-04-16", "wednesday", 7)
        assert result == "23/04"


class TestGetFullDateForWeekday:
    """Test get_full_date_for_weekday function."""

    def test_returns_full_date_label(self):
        """Should return weekday name and date."""
        result = get_full_date_for_weekday("2026-04-16", 0)
        assert result == "Jeudi 16/04"

        result = get_full_date_for_weekday("2026-04-16", 1)
        assert result == "Vendredi 17/04"

        result = get_full_date_for_weekday("2026-04-16", 7)
        assert result == "Jeudi 23/04"


class TestGetPeriodFromDate:
    """Test get_period_from_date function."""

    def test_returns_period_for_date_in_middle(self):
        """Should return correct period for date in the middle."""
        result = get_period_from_date("2026-04-20")  # Monday
        assert result["start_date"] == "2026-04-16"
        assert result["end_date"] == "2026-04-23"
        assert result["period_id"] == "2026-04-16"
        assert result["display_label"] == "16/04 - 23/04"

    def test_returns_period_for_thursday(self):
        """Should return correct period for Thursday (start of period)."""
        result = get_period_from_date("2026-04-16")
        assert result["start_date"] == "2026-04-16"
        assert result["end_date"] == "2026-04-23"

    def test_returns_period_for_wednesday(self):
        """Should return correct period for Wednesday (end of period)."""
        result = get_period_from_date("2026-04-22")
        assert result["start_date"] == "2026-04-16"
        assert result["end_date"] == "2026-04-23"

    def test_returns_previous_period_for_early_month_date(self):
        """Should handle dates that belong to previous period."""
        # 2026-04-15 is a Wednesday, belongs to period starting 2026-04-09
        result = get_period_from_date("2026-04-15")
        assert result["start_date"] == "2026-04-09"
        assert result["end_date"] == "2026-04-16"
