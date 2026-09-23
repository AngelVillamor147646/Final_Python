"""Utils package — re-exports for convenient imports."""
from utils.logger import get_logger
from utils.date_utils import (
    today, now, fmt_date, fmt_time, fmt_datetime,
    display_date, display_datetime, parse_date, parse_time, parse_datetime,
    days_until, is_today, is_overdue, week_dates, day_name,
    start_of_week, end_of_week, start_of_month, end_of_month,
    minutes_to_hm, duration_minutes, time_range_overlaps, iso_week_number,
)
from utils.helpers import (
    slugify, truncate, pluralise, hex_to_kivy_colour, kivy_colour_to_hex,
    safe_json_loads, safe_json_dumps, ensure_dir, clamp, percentage, lerp,
    is_android, is_windows, new_uuid, safe_filename, initials,
)
from utils.validation import (
    validate_required, validate_length, validate_name,
    validate_positive_int, validate_range, validate_date_not_past,
    validate_time_order, validate_hex_colour, validate_file_extension,
    validate_card_count, sanitize_markdown, ok, err,
)

__all__ = [
    "get_logger",
    "today", "now", "fmt_date", "fmt_time", "fmt_datetime",
    "display_date", "display_datetime", "parse_date", "parse_time",
    "parse_datetime", "days_until", "is_today", "is_overdue",
    "week_dates", "day_name", "start_of_week", "end_of_week",
    "start_of_month", "end_of_month", "minutes_to_hm",
    "duration_minutes", "time_range_overlaps", "iso_week_number",
    "slugify", "truncate", "pluralise", "hex_to_kivy_colour",
    "kivy_colour_to_hex", "safe_json_loads", "safe_json_dumps",
    "ensure_dir", "clamp", "percentage", "lerp", "is_android",
    "is_windows", "new_uuid", "safe_filename", "initials",
    "validate_required", "validate_length", "validate_name",
    "validate_positive_int", "validate_range", "validate_date_not_past",
    "validate_time_order", "validate_hex_colour", "validate_file_extension",
    "validate_card_count", "sanitize_markdown", "ok", "err",
]
