from datetime import date, datetime
from typing import Optional, Tuple


def parse_iso_date(value, field_name: str) -> date:
    # convert request date strings into date objects with a clear error message
    try:
        return datetime.fromisoformat(str(value)).date()
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be a valid ISO date") from exc


def parse_date_range(
    start_value,
    end_value,
    *,
    start_field: str = "start_date",
    end_field: str = "end_date",
    require_both: bool = True,
    normalize_order: bool = False,
) -> Tuple[Optional[date], Optional[date]]:
    # shared helper for endpoints that accept optional start/end date filters
    if start_value is None and end_value is None:
        return None, None

    if require_both and (start_value is None or end_value is None):
        raise ValueError(f"{start_field} and {end_field} must be provided together")

    start_date = parse_iso_date(start_value, start_field)
    end_date = parse_iso_date(end_value, end_field)

    if start_date > end_date:
        if normalize_order:
            # dashboard filters can be forgiving and swap reversed dates
            return end_date, start_date
        raise ValueError(f"{start_field} must be on or before {end_field}")

    return start_date, end_date
