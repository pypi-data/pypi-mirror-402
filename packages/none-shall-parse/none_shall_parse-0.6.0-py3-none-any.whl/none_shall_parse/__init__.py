"""Trinity Shared Python utilities.

A collection of shared utilities for Trinity projects.

Originally intended to be parsing utilities, this grew to include
other useful functions.

Named for its author Andries Niemandt - whose surname loosely
translates to "none". Combined this with our parsing intentions
to create a name which nods to the Black Knight in Monty Python's Holy Grail.
https://www.youtube.com/watch?v=zKhEw7nD9C4
"""
from __future__ import annotations
from .dates import (
    DateUtilsError, assert_week_start_date_is_valid,
    assert_month_start_date_is_valid,
    get_datetime_now, za_now, utc_now,
    za_ordinal_year_day_now,
    za_ordinal_year_day_tomorrow, utc_epoch_start,
    now_offset_n_minutes, now_offset_n_hours,
    now_offset_n_days, now_offset_n_months, get_datetime_tomorrow,
    get_datetime_yesterday,
    get_utc_datetime_offset_n_days,
    epoch_to_datetime, epoch_to_utc_datetime,
    is_office_hours_in_timezone,
    get_datetime_from_ordinal_and_sentinel,
    day_span, week_span, month_span, arb_span,
    calendar_month_start_end, unix_timestamp,
    sentinel_date_and_ordinal_to_date,
    seconds_to_end_of_month, standard_tz_timestring,
    get_notice_end_date, dt_to_za_time_string,
    months_ago_selection, is_aware, make_aware,
    unaware_to_utc_aware, timer_decorator, ZA_TZ,
    UTC_TZ, keys_for_span_func,
)
from .imeis import (
    get_luhn_digit,
    is_valid_luhn,
    is_valid_imei,
    normalize_imei,
    get_tac_from_imei,
    decrement_imei,
    increment_imei,
)

from .lists import (
    flatten,
    safe_list_get,
)
from .parse import (
    str_to_bool,
    is_true,
    is_false,
    str_to_strs_list,
    int_to_bool,
    int_or_none,
    choices_code_to_string,
    choices_string_to_code,
    none_or_empty,
)
from .strings import (
    slugify,
    random_16,
    to_human_string,
    is_quoted_string,
    is_numeric_string,
    custom_slug,
    b64_encode,
    b64_decode,
    calc_hash,
    generate_random_password,
)
from .types import (
    StringLike,
    ChoicesType,
    DateTimeLike,
    DateLike,
    DateTimeOrDateLike,
)

__author__ = "Andries Niemandt, Jan Badenhorst"
__email__ = "andries.niemandt@trintel.co.za, jan@trintel.co.za"
__license__ = "MIT"

__all__ = (
    "DateUtilsError", "assert_week_start_date_is_valid",
    "assert_month_start_date_is_valid",
    "get_datetime_now", "za_now", "utc_now",
    "za_ordinal_year_day_now",
    "za_ordinal_year_day_tomorrow", "utc_epoch_start",
    "now_offset_n_minutes", "now_offset_n_hours",
    "now_offset_n_days", "now_offset_n_months", "get_datetime_tomorrow",
    "get_datetime_yesterday",
    "get_utc_datetime_offset_n_days",
    "epoch_to_datetime", "epoch_to_utc_datetime",
    "is_office_hours_in_timezone",
    "get_datetime_from_ordinal_and_sentinel",
    "day_span", "week_span", "month_span", "arb_span",
    "calendar_month_start_end", "unix_timestamp",
    "sentinel_date_and_ordinal_to_date",
    "seconds_to_end_of_month", "standard_tz_timestring",
    "get_notice_end_date", "dt_to_za_time_string",
    "months_ago_selection", "is_aware", "make_aware",
    "unaware_to_utc_aware", "timer_decorator", "ZA_TZ",
    "UTC_TZ", "keys_for_span_func",
    "get_luhn_digit",
    "is_valid_luhn",
    "is_valid_imei",
    "normalize_imei",
    "get_tac_from_imei",
    "decrement_imei",
    "increment_imei",
    "flatten",
    "safe_list_get",
    "str_to_bool",
    "is_true",
    "is_false",
    "str_to_strs_list",
    "int_to_bool",
    "int_or_none",
    "choices_code_to_string",
    "choices_string_to_code",
    "none_or_empty",
    "slugify",
    "random_16",
    "to_human_string",
    "is_quoted_string",
    "is_numeric_string",
    "custom_slug",
    "b64_encode",
    "b64_decode",
    "calc_hash",
    "generate_random_password",
    "StringLike",
    "ChoicesType",
    "DateTimeLike",
    "DateLike",
    "DateTimeOrDateLike",
)