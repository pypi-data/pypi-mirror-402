import functools
import logging
import time
from datetime import date, datetime
from typing import Callable, Any, Tuple, Sequence, List
from .types import DateTimeLike

import pendulum
from pendulum import DateTime, Date
from pendulum import local_timezone
from pendulum.tz.exceptions import InvalidTimezone

ZA_TZ = 'Africa/Johannesburg'
UTC_TZ = 'UTC'


class DateUtilsError(Exception):
    """
    Raised when some date calc gets crap input.
    """

    message = None

    def __init__(self, message):
        super().__init__(message)
        self.message = message


def assert_week_start_date_is_valid(wso: int) -> None:
    if wso < 1 or wso > 7:
        raise DateUtilsError("Weeks can only start on days between 1 and 7")


def assert_month_start_date_is_valid(mso: int) -> None:
    if mso > 28 or mso < 1:
        raise DateUtilsError("Months can only start on days between 1 and 28")


def get_datetime_now(naive: bool = False, tz: str | None = None) -> DateTime:
    """
    Get the current date and time.

    This function retrieves the current date and time using the pendulum library. It can
    return the DateTime in either a naive or timezone-aware format, depending on the
    parameters provided.

    Args:
        naive (bool): If True, returns a naive DateTime object without timezone information.
                      Defaults to True.
        tz (Optional[str]): The timezone to use if a timezone-aware DateTime is requested.
                            If not provided and naive is False, the default system timezone
                            is used.

    Returns:
        pendulum.DateTime: The current date and time based on the specified parameters.
    """
    return pendulum.now().naive() if naive else pendulum.now(tz=tz)


def za_now() -> DateTime:
    """
    Returns the current date and time in the South African timezone.

    This function retrieves the current date and time, ensuring it is aware of
    time zone settings. It uses the South African timezone (ZA_TZ) for proper
    time localization.

    Returns:
        pendulum.DateTime: The current date and time in the South African timezone.
    """
    return get_datetime_now(naive=False, tz=ZA_TZ)


def utc_now() -> DateTime:
    """
    Shorthand for the current date and time in the UTC timezone.
    Returns:
        pendulum.DateTime: The current date and time in the UTC timezone.
    """
    return get_datetime_now(naive=False, tz=UTC_TZ)


def za_ordinal_year_day_now() -> int:
    """
    Returns the current ordinal day of the year for the ZA_TZ timezone.

    This function calculates and returns the day of the year based on the current
    date and time in the ZA (South Africa) timezone.

    Returns:
        int: The current ordinal day of the year in ZA_TZ timezone.
    """
    return pendulum.now(ZA_TZ).day_of_year


def za_ordinal_year_day_tomorrow() -> int:
    """
    Returns the ordinal day of the year for tomorrow in the ZA_TZ timezone.

    This function calculates the ordinal day of the year (1 to 366) for the date
    that is one day ahead of today, as per the ZA_TZ timezone.

    Returns:
        int: The ordinal day of the year for tomorrow in the ZA_TZ timezone.
    """
    return pendulum.now(ZA_TZ).add(days=1).day_of_year


def utc_epoch_start() -> DateTime:
    """
    Gets the UTC epoch start time as a DateTime object.

    This function calculates the start of the UNIX epoch (January 1, 1970)
    in UTC as a DateTime object. It leverages the `pendulum` library for
    handling the time calculation with the specified UTC timezone.

    Returns:
        pendulum.DateTime: A pendulum DateTime object representing the start of the UTC epoch.
    """
    return pendulum.from_timestamp(0)


def _now_offset_n_units(n: int, units: str, naive: bool = False,
                        tz: str | None = None) -> DateTime:
    """
    Calculate a DateTime object offset by a specified number of time units.

    This function allows you to calculate a DateTime offset by a given number of units
    (minutes, hours, days, etc.) from the current time. You can also specify the timezone
    and whether the returned DateTime should be naive or timezone-aware.

    Parameters:
        n (int): The number of units to offset the current time by.
        units (str): The type of time unit to offset by.
        naive (bool): Whether to return a naive DateTime (without timezone information).
            Defaults to False.
        tz (Optional[str]): The timezone of the resulting DateTime. If not provided,
            the system's local timezone is used.

    Returns:
        DateTime: The calculated DateTime object, optionally timezone-aware or naive.
    """
    kwargs = {units: n}
    return pendulum.now().add(**kwargs).naive() if naive else pendulum.now(tz).add(
        **kwargs)


def now_offset_n_minutes(n: int, naive: bool = False,
                         tz: str | None = None) -> DateTime:
    return _now_offset_n_units(n, units="minutes", naive=naive, tz=tz)


def now_offset_n_hours(n: int, naive: bool = False,
                       tz: str | None = None) -> DateTime:
    return _now_offset_n_units(n, units="hours", naive=naive, tz=tz)


def now_offset_n_days(n: int, naive: bool = False,
                      tz: str | None = None) -> DateTime:
    return _now_offset_n_units(n, units="days", naive=naive, tz=tz)


def now_offset_n_months(n: int, naive: bool = False, tz: str | None = None) -> DateTime:
    return _now_offset_n_units(n, units="months", naive=naive, tz=tz)


def get_datetime_tomorrow(naive: bool = False,
                          tz: str | None = None) -> DateTime:
    """Get tomorrow's DateTime"""
    return now_offset_n_days(1, naive=naive, tz=tz)


def get_datetime_yesterday(naive: bool = False,
                           tz: str | None = None) -> DateTime:
    """Get yesterday's DateTime"""
    return now_offset_n_days(-1, naive=naive, tz=tz)


def get_utc_datetime_offset_n_days(n: int = 0) -> DateTime:
    """Get UTC DateTime n with an offset of n days"""
    return pendulum.now(UTC_TZ).add(days=n)


def epoch_to_datetime(epoch_int: int | float, naive: bool = False,
                      tz: str | None = None) -> DateTime:
    """
    Converts an epoch timestamp to a DateTime object.

    This function takes an input epoch timestamp and converts it into a
    DateTime object using the Pendulum library. It supports conversion
    to either naive or timezone-aware DateTime objects based on the
    parameters provided.

    Parameters:
        epoch_int (int | float): The epoch timestamp to convert to a DateTime
            object. It can be provided as an integer or float value.
        naive (bool): If True, the resulting DateTime object will be naive
            (without timezone information). Defaults to False.
        tz (Optional[str]): The timezone in which the resulting DateTime object
            should be created. If not provided, the system's default timezone
            will be used.

    Returns:
        DateTime: A DateTime object representing the converted epoch timestamp.
    """

    # We force the timezone to the user's local timezone if none was supplied
    # to make this function behave the same as the other functions, where the absense
    # of a timezone is interpreted as the user's local timezone.'
    if tz is None:
        tz = local_timezone()

    if naive:
        return pendulum.from_timestamp(int(epoch_int), tz=tz).naive()
    return pendulum.from_timestamp(int(epoch_int), tz=tz)


def epoch_to_utc_datetime(epoch_int: int | float | str) -> DateTime:
    """
    Converts an epoch timestamp to a UTC DateTime object.

    This function takes an integer or float representing an epoch timestamp,
    and converts it to a DateTime object in UTC timezone using Pendulum.

    Parameters:
        epoch_int: An epoch timestamp represented as an integer or float.

    Returns:
        A DateTime object in UTC corresponding to the provided epoch timestamp.
    """
    return pendulum.from_timestamp(int(epoch_int), tz=UTC_TZ)


def is_office_hours_in_timezone(epoch_int: int | float | str, tz: str | None = None) -> bool:
    """
    Determines if a given epoch timestamp falls within office hours for a
    specific timezone.

    Office hours are considered to be between 08:00 and 17:00 (8 AM to 5 PM) in
    the specified timezone. The function converts the provided epoch timestamp into
    a DateTime object according to the given timezone and checks whether the time falls
    within the defined office hours.

    Parameters:
        epoch_int: int | float
            Epoch timestamp to be checked. It must represent the number of seconds
            (or fraction of seconds, if float) since the UNIX epoch.
        tz: str, optional
            Timezone expressed as a string. Defaults to local system timezone.

    Returns:
        bool
            True if the epoch timestamp occurs within office hours for the specified
            timezone otherwise, False.
    """
    dt = pendulum.from_timestamp(int(epoch_int), tz=tz)

    # Create office hours boundaries for the same date
    oh_begin = dt.replace(hour=8, minute=0, second=0, microsecond=0)
    oh_end = dt.replace(hour=17, minute=0, second=0, microsecond=0)

    return oh_begin < dt < oh_end


def get_datetime_from_ordinal_and_sentinel(
        sentinel: DateTimeLike | None = None) -> Callable[[int], DateTime]:
    """
    Given an ordinal year day, and a sentinel datetime, get the closest past
    datetime to the sentinel that had the given ordinal year day.

    If the given sentinel is timezone-aware, the results will be as well, and in the
    same timezone. If the given sentinel is naive, the results will be naive.
    """
    # Check timezone awareness
    naive = sentinel.tzinfo is None
    sentinel = pendulum.instance(sentinel)
    if naive:
        sentinel = sentinel.naive()
    sentinel_doy = sentinel.day_of_year
    sentinel_year = sentinel.year

    if naive:
        this_year = pendulum.naive(sentinel_year, 1, 1)
        last_year = pendulum.naive(sentinel_year - 1, 1, 1)
    else:
        this_year = pendulum.datetime(sentinel_year, 1, 1, tz=sentinel.timezone)
        last_year = pendulum.datetime(sentinel_year - 1, 1, 1, tz=sentinel.timezone)

    def f(ordinal: int) -> DateTime:
        dt = this_year if ordinal <= sentinel_doy else last_year

        # Handle leap year edge case
        if ordinal == 366 and not dt.is_leap_year():
            if naive:
                return pendulum.naive(1970, 1, 1)
            else:
                return pendulum.datetime(1970, 1, 1, tz=sentinel.timezone)

        result = dt.add(days=ordinal - 1)
        return result

    return f


# ------------------------------------------------------------------[ Span Functions ]--
def day_span(pts: DateTimeLike) -> Tuple[DateTime, DateTime]:
    """
    Returns the beginning and end of the day passed in.
    begin is inclusive and end is exclusive.

    If the given datetime is timezone aware, the results will be as well, and in the
    same timezone. If the given sentinel is naive, the results will be naive.

    Examples:
        from datetime import datetime
        dt = datetime(2023, 12, 25, 14, 30, 45)

        start, end = day_span(dt)
        print(type(start)) # <class 'DateTime.DateTime'>

    """
    # Check if input is naive or aware
    naive = pts.tzinfo is None
    pdt = pendulum.instance(pts)

    # Use Pendulum's clean API
    begin = pdt.start_of('day')
    end = pdt.add(days=1).start_of('day')

    if naive:
        return begin.naive(), end.naive()
    else:
        return begin, end


def week_span(wso: int) -> Callable[[DateTimeLike], Tuple[DateTime, DateTime]]:
    """
    Given an integer between 1 and 7, return a function that will give the
    start and end dates of the week.

    If the given datetime is timezone aware, the results will be as well, and in the
    same timezone. If the given sentinel is naive, the results will be naive.

    Examples:
        from datetime import datetime
        dt = datetime(2023, 12, 25, 14, 30, 45)

        # Week starting on Wednesday (ISO day 3)
        week_func = week_span(3)
        week_start, week_end = week_func(dt)

    :param wso: ISO weekday integer (1=Monday, 7=Sunday)
    """
    assert_week_start_date_is_valid(wso)

    def find_dates(pts: DateTimeLike) -> Tuple[DateTime, DateTime]:
        # Check if input is naive or aware
        naive = pts.tzinfo is None
        pdt = pendulum.instance(pts)

        # Get to the desired week start day
        current_weekday = pdt.weekday() + 1  # Pendulum uses 0-6, we want 1-7
        days_back = (current_weekday - wso) % 7

        begin = pdt.start_of('day').subtract(days=days_back)
        end = begin.add(days=7)

        if naive:
            return begin.naive(), end.naive()
        else:
            return begin, end

    return find_dates


def month_span(mso: int) -> Callable[[DateTimeLike], Tuple[DateTime, DateTime]]:
    """
    Given an integer between 1 and 28, return a function that will give the
    start and end dates of the custom month period.

    If the given datetime is timezone aware, the results will be as well, and in the
    same timezone. If the given sentinel is naive, the results will be naive.

    Examples:
        from datetime import datetime
        dt = datetime(2023, 12, 25, 14, 30, 45)

        # Month starting on 15th
        month_func = month_span(15)
        month_start, month_end = month_func(dt)

    :param mso: Integer (1-28, the day of month to start periods on)
    """
    assert_month_start_date_is_valid(mso)

    def find_dates(pts: DateTimeLike) -> Tuple[DateTime, DateTime]:
        # Convert to Pendulum
        naive = pts.tzinfo is None
        pdt = pendulum.instance(pts)
        current_day = pdt.day

        if current_day >= mso:
            # We're in the current month period
            begin = pdt.start_of('day').replace(day=mso)
        else:
            # We're in the previous month period
            begin = pdt.start_of('day').subtract(months=1).replace(day=mso)

        # End is mso of next month from `begin`
        end = begin.add(months=1)

        if naive:
            return begin.naive(), end.naive()
        else:
            return begin, end

    return find_dates


def arb_span(dates: Sequence[str | DateTimeLike], naive: bool = False) -> Callable[
    [Any], Tuple[DateTime, DateTime]]:
    """
    Parses two given dates and returns a callable function that provides the date range
    as a tuple of datetime objects. The function ensures the date range is valid and
    always returns the earlier date as the start and the later date as the end.

    Parameters:
        dates (Sequence[str | DateTimeLike]): A sequence containing exactly two dates where
            each date is either a string or a datetime object.
        naive (bool): Optional flag. If True, the returned datetime objects will not
            have timezone information (naive datetime). Defaults to False.

    Returns:
        Callable[[Any], Tuple[DateTime, DateTime]]: A function that, when invoked,
        returns a tuple of DateTime objects (start, end) representing the date range.

    Raises:
        DateUtilsError: If the provided dates are invalid, identical, or there's an error
       during parsing.
    """
    try:
        parsed_dates = []

        for date in dates[:2]:
            if isinstance(date, str):
                # Parse string - pendulum.parse returns UTC for date-only strings
                parsed = pendulum.parse(date)

                # If it's a date-only string (no time/timezone info), treat as naive
                if 'T' not in date and ' ' not in date:
                    parsed = parsed.naive()

                parsed_dates.append(parsed.start_of('day'))
            else:
                # It's already a datetime
                if date.tzinfo is None:
                    # Input is naive, keep it naive using pendulum.naive()
                    parsed = pendulum.naive(date.year, date.month, date.day,
                                            date.hour, date.minute, date.second,
                                            date.microsecond)
                else:
                    # Input is timezone-aware, preserve it
                    parsed = pendulum.instance(date)

                parsed_dates.append(parsed.start_of('day'))

        a, b = parsed_dates

        # Check if they're comparable (both naive or both aware)
        if (a.tzinfo is None) != (b.tzinfo is None):
            raise DateUtilsError("Cannot compare naive and timezone-aware datetimes")

        if a == b:
            raise DateUtilsError("Dates may not be the same")

        # Ensure `begin` is the earlier date and `end` is the later date
        begin = a if a < b else b
        end = b if a < b else a

    except Exception as ex:
        raise DateUtilsError(f"Error parsing dates: {ex}")

    def find_dates(*args) -> Tuple[DateTime, DateTime]:
        """
        :return: tuple of DateTime objects (start, end)
        """
        if naive:
            return begin.naive(), end.naive()
        return begin, end

    return find_dates


def unroll_span_func(
        f: Callable[[DateTimeLike], Tuple[DateTime, DateTime]],
        cover: DateTimeLike | None = None,
) -> Tuple[List[DateTime], List[int], List[str], DateTime, DateTime]:
    """
    Generate keys for a date range based on a provided function.

    This function computes a date range using the provided function `f`, which takes a base date and returns
    start and end dates. It generates input and output keys for each day in the range based on ordinal days
    and optionally returns only ordinal day integers.

    Args:
        f: Function that takes a base date and returns a tuple of start and end dates.
        cover: Base datetime for computing the range. Defaults to the current date if None.

    Returns:
        A tuple containing:
        - List of DateTime objects.
        - List of ordinal day integers.
        - Start date of the range (as DateTime).
        - End date of the range (as DateTime).
        If ord_ints_only is True, returns (ordinal_days, start, end, iso_dates).

    Raises:
        DateUtilsError: If the date range cannot be processed due to invalid dates or formatting.
    """
    cover = pendulum.now() if cover is None else cover

    try:
        start, end = f(cover)
        start = pendulum.instance(start)
        end = pendulum.instance(end)

        # Determine naiveness from the dates returned by f, not from cover
        naive = start.tzinfo is None
        if naive:
            start = start.naive()
            end = end.naive()

        # Get actual current time for filtering future dates (always "now", not cover)
        current_date_sentinel = pendulum.now().naive() if naive else pendulum.now()

    except Exception as e:
        raise DateUtilsError(f"Function f failed to compute date range: {str(e)}")

    try:
        # Generate date range using pendulum.interval
        # The absolute kwarg ensures that we do not have to care about dates passed
        # in the wrong order. We will always range from start to end, inclusive.
        interval = pendulum.interval(start, end.subtract(days=1), absolute=True)
        date_range = []
        ord_days = []
        iso_date_strings = []
        for dt in interval.range(unit="days"):
            # Filter: only include dates up to today (not future dates)
            if dt <= current_date_sentinel and dt < end:
                date_range.append(dt)
                ord_days.append(dt.day_of_year)
                iso_date_strings.append(dt.format('YYYY-MM-DD'))

        return date_range, ord_days, iso_date_strings, start, end

    except (TypeError, ValueError) as e:
        raise DateUtilsError(f"Error processing date range: {str(e)}")


def keys_for_span_func(
        f: Callable[[DateTimeLike], Tuple[DateTime, DateTime]],
        cover: DateTimeLike | None = None,
        key_in_format: str = "ODIN_{}",
        key_out_format: str = "ODOUT_{}",
):
    """
    Generate keys for a date range based on a provided function.

    Args:
        f: Function that takes a base date and returns a tuple of start and end dates.
        cover: Base date for computing the range. Defaults to the current date if None.
        key_in_format: Format string for input keys. Defaults to "ODIN_{}".
        key_out_format: Format string for output keys, Defaults to "ODOUT_{}"

    Returns:
        - List of input keys (empty if key_in_format is None).
        - List of output keys (empty if key_out_format is None).
        - Start date of the range (as DateTime).
        - End date of the range (as DateTime).

    Raises:
        DateUtilsError: If the date range cannot be processed.
    """
    date_range, ord_days, iso_date_strings, start, end = unroll_span_func(f=f, cover=cover)
    keys_in = [key_in_format.format(d) for d in ord_days]
    keys_out = [key_out_format.format(d) for d in ord_days]
    return keys_in, keys_out, start, end


def calendar_month_start_end(date_in_month: DateTimeLike | None = None) -> Tuple[
    DateTime, DateTime]:
    naive = date_in_month.tzinfo is None

    if date_in_month is None:
        date_in_month = za_now()

    pdt = pendulum.instance(date_in_month)

    start = pdt.start_of('month')
    end = start.add(months=1)

    if naive:
        return start.naive(), end.naive()

    return start, end


# --------------------------------------------------------------------[ Unaware time ]--
def unix_timestamp() -> int:
    """
    Unix timestamps are, by definition, the number of seconds since the epoch - a
    fixed moment in time, defined as 01-01-1970 UTC.
    :return: Current Unix timestamp
    """
    return round(time.time())


def sentinel_date_and_ordinal_to_date(sentinel_date: DateTimeLike | date,
                                      ordinal: int | float | str) -> date:
    """Convert sentinel date and ordinal day to actual date"""
    year = sentinel_date.year
    int_ordinal = int(ordinal)

    # If sentinel is Jan 1st and ordinal > 1, use previous year
    if sentinel_date.month == 1 and sentinel_date.day == 1 and int_ordinal > 1:
        year = year - 1

    # Use Pendulum for date arithmetic
    dt = pendulum.datetime(year, 1, 1).add(days=int_ordinal - 1)
    return dt.date()


def seconds_to_end_of_month() -> int:
    """Calculate seconds remaining until the end of the current month"""
    now = pendulum.now(UTC_TZ)
    end_of_month = now.end_of('month')
    return int((end_of_month - now).total_seconds())


def standard_tz_timestring(ts: int | float, tz: str = ZA_TZ) -> str:
    """
    Format timestamp as: 2022-02-22 15:28:10 (SAST)
    :param ts: Seconds since epoch
    :param tz: Timezone string
    :return: Formatted date time string
    """
    dt = pendulum.from_timestamp(int(ts), tz=tz)
    return dt.strftime("%Y-%m-%d %H:%M:%S (%Z)")


def get_notice_end_date(given_date: DateTimeLike | date | Date | None = None) -> Date:
    """
    A notice end date is the end of the month of the given date if the given date
    is before or on the 15th. If the given date is after the 15th, the notice period
    ends at the end of the next month.
    :param given_date: Date to calculate the notice end from
    :return: Notice end date
    """
    if given_date is None:
        given_date = pendulum.now().today()
    elif isinstance(given_date, datetime):
        given_date = given_date.date()
    elif not isinstance(given_date, date):
        raise ValueError(
            "Given date must be a datetime.date or datetime.datetime object")

    pdt = pendulum.instance(given_date)
    if given_date.day <= 15:
        # End of current month
        end_date = pdt.add(months=1).start_of('month')
    else:
        # End of next month
        end_date = pdt.add(months=2).start_of('month')

    if isinstance(end_date, DateTime):
        return end_date.date()
    return end_date


def dt_to_za_time_string(v: DateTimeLike) -> str:
    """Convert DateTime to South Africa time string"""
    # Convert to Pendulum
    naive = v.tzinfo is None
    if naive:
        pdt = pendulum.instance(v, tz=ZA_TZ)
    else:
        pdt = pendulum.instance(v).in_timezone(ZA_TZ)
    return pdt.strftime("%Y-%m-%d %H:%M:%S")


def months_ago_selection() -> List[Tuple[int, str]]:
    """Generate list of (index, "Month-Year") tuples for last 12 months"""
    today = pendulum.today()

    return [
        (i, today.subtract(months=i).strftime("%B-%Y"))
        for i in range(12)
    ]


def is_aware(dt: DateTimeLike | Date | date) -> bool:
    """Check if a DateTime object is timezone-aware."""
    return dt.tzinfo is not None and dt.tzinfo.utcoffset(dt) is not None


def make_aware(dt: DateTimeLike | date | Date | None, tz: str = None) -> DateTime | Date | None:
    """
    Convert a naive DateTime to a timezone-aware DateTime using Pendulum.

    Args:
        dt: The DateTime object to convert. If None, returns None.
        tz: The timezone to apply (default: The user's default timezone).).

    Returns:
        A timezone-aware DateTime object.

    Raises:
        TypeError: If dt is not a DateTime object or None.
        ValueError: If dt is already timezone-aware.
        DateUtilsError: If the timezone string is invalid.
    """
    # We force the timezone to the user's local timezone if none was supplied
    # to make this function behave the same as the other functions, where the absense
    # of a timezone is interpreted as the user's local timezone.
    if tz is None:
        tz = local_timezone()

    if dt is None:
        return None
    if not isinstance(dt, datetime):
        raise TypeError(f"Expected datetime or None, got {type(dt).__name__}")
    if is_aware(dt):
        raise ValueError(f"Datetime is already timezone-aware with {dt.tzinfo}")

    try:
        return pendulum.instance(dt, tz=tz)
    except InvalidTimezone as e:
        raise DateUtilsError(f"Invalid timezone: {tz}") from e


def unaware_to_utc_aware(dt: DateTimeLike | date | Date | None) -> DateTime | Date | None:
    """Convert naive DateTime to UTC-aware DateTime using Pendulum."""
    if not isinstance(dt, (datetime, type(None))):
        raise TypeError(f"Expected datetime or None, got {type(dt)}")

    if dt is None or is_aware(dt):
        return dt

    # Use Pendulum for clean UTC conversion
    pdt = pendulum.instance(dt, tz=UTC_TZ)
    return pdt


def timer_decorator(logger: logging.Logger | None = None):
    """
    Timer decorator that optionally accepts a logger.

    Args:
        logger: Logger instance to use for timing output. If None, uses print().

    Returns:
        Decorator function
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.perf_counter()
            result = func(*args, **kwargs)
            end_time = time.perf_counter()
            execution_time = end_time - start_time

            message = f"{func.__name__}:TIME:{execution_time:.6f}s"

            if logger:
                logger.info(message)
            else:
                print(message)  # Fallback to print if no logger provided

            return result

        return wrapper

    return decorator
