from datetime import datetime, date
from datetime import timedelta
import calendar
import numpy as np
import re

dt_fmt = "%Y-%m-%d"
dtm_fmt = "%Y-%m-%d %H:%M:%S"
is_utc = True

class Cdt:

    def set_is_utc(self, is_utc=True):
        self.is_utc = is_utc

    def __init__(self, dt_fmt=dt_fmt, dtm_fmt=dtm_fmt):
        self.dt_fmt = dt_fmt
        self.dtm_fmt = dtm_fmt
        self.is_utc = True

    _UNIT_SECONDS = {
        # seconds
        "s": 1, "sec": 1, "secs": 1, "second": 1, "seconds": 1,
        # minutes
        "m": 60, "min": 60, "mins": 60, "minute": 60, "minutes": 60,
        # hours
        "h": 3600, "hr": 3600, "hrs": 3600, "hour": 3600, "hours": 3600,
        # days
        "d": 86400, "day": 86400, "days": 86400,
        # weeks
        "w": 604800, "wk": 604800, "wks": 604800, "week": 604800, "weeks": 604800,
    }

    def _parse_duration_to_timedelta(self, duration_string: str) -> timedelta:
        """
        Parses strings like:
          "30 days", "2 weeks", "1 week", "5 hours", "5 hrs", "40 mins", "10 secs"
        into a timedelta.
        """
        if not duration_string or not isinstance(duration_string, str):
            raise ValueError("duration_string must be a non-empty string")

        s = duration_string.strip().lower()
        # allow "30days" too
        m = re.fullmatch(r"([+-]?\d+(?:\.\d+)?)\s*([a-z]+)", s)
        if not m:
            raise ValueError(f"Invalid duration format: {duration_string!r}. Expected e.g. '30 days', '5 hrs'.")

        qty = float(m.group(1))
        unit = m.group(2)

        if unit not in self._UNIT_SECONDS:
            raise ValueError(
                f"Unsupported unit {unit!r}. Supported: seconds/minutes/hours/days/weeks (and common aliases)."
            )

        total_seconds = qty * self._UNIT_SECONDS[unit]
        return timedelta(seconds=total_seconds)

    def _quarter_start_end(self, d: date):
        q = ((d.month - 1) // 3) + 1  # 1..4
        start_month = (q - 1) * 3 + 1
        q_start = date(d.year, start_month, 1)

        # next quarter start then -1 day
        if q == 4:
            next_q_start = date(d.year + 1, 1, 1)
        else:
            next_q_start = date(d.year, start_month + 3, 1)

        q_end = next_q_start - timedelta(days=1)
        return q_start, q_end

    def _resolve_anchor_to_date_str(self, anchor: str) -> str:
        """
        Converts anchor phrases to a YYYY-MM-DD date string.

        Supported anchors (case-insensitive, whitespace-insensitive):
          today, yesterday

          week start, week end
          last week start, last week end
          previous week start, previous week end

          month start, month end
          last month start, last month end
          previous month start, previous month end

          quarter start, quarter end
          last quarter start, last quarter end
          previous quarter start, previous quarter end
        """
        if not anchor or not isinstance(anchor, str):
            raise ValueError("anchor must be a non-empty string")

        a = re.sub(r"\s+", " ", anchor.strip().lower())

        # direct date literal
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", a):
            return a

        if a == "today":
            return self.today()

        if a == "yesterday":
            return self.yesterday()

        # ---------- week ----------
        if a in ("week start", "current week start"):
            return self.fn_week_tuple(self.today())[0]

        if a in ("week end", "current week end"):
            return self.fn_week_tuple(self.today())[1]

        if a in ("last week start", "previous week start"):
            return self.week_x(1)[0]

        if a in ("last week end", "previous week end"):
            return self.week_x(1)[1]

        # ---------- month ----------
        if a in ("month start", "current month start"):
            return self.fn_first_day_of_month(self.today())

        if a in ("month end", "current month end"):
            return self.fn_last_day_of_month(self.today())

        if a in ("last month start", "previous month start"):
            return self.month_x(1)[0]

        if a in ("last month end", "previous month end"):
            return self.month_x(1)[1]

        # ---------- quarter ----------
        today_d = datetime.strptime(self.today(), self.dt_fmt).date()

        if a in ("quarter start", "current quarter start"):
            qs, _ = self._quarter_start_end(today_d)
            return qs.strftime(self.dt_fmt)

        if a in ("quarter end", "current quarter end"):
            _, qe = self._quarter_start_end(today_d)
            return qe.strftime(self.dt_fmt)

        if a in ("last quarter start", "previous quarter start"):
            qs, _ = self._quarter_start_end(today_d)
            prev_q_end = qs - timedelta(days=1)
            prev_qs, _ = self._quarter_start_end(prev_q_end)
            return prev_qs.strftime(self.dt_fmt)

        if a in ("last quarter end", "previous quarter end"):
            qs, _ = self._quarter_start_end(today_d)
            prev_q_end = qs - timedelta(days=1)
            _, prev_qe = self._quarter_start_end(prev_q_end)
            return prev_qe.strftime(self.dt_fmt)

        raise ValueError(
            f"Unsupported anchor: {anchor!r}. "
            f"Try: today, yesterday, week start/end, last week start/end, "
            f"month start/end, last month start/end, quarter start/end, last quarter start/end."
        )

    def dateminusduration(self, input_date: str, duration_string: str) -> str:
        """
        input_date: "YYYY-MM-DD"
        duration_string: "30 days", "2 weeks", "5 hours", etc.
        Returns: "YYYY-MM-DD" (date only).
        """
        base = datetime.strptime(input_date, self.dt_fmt)  # midnight
        delta = self._parse_duration_to_timedelta(duration_string)
        out = base - delta
        return out.strftime(self.dt_fmt)

    def dateplusduration(self, input_date: str, duration_string: str) -> str:
        base = datetime.strptime(input_date, self.dt_fmt)
        delta = self._parse_duration_to_timedelta(duration_string)
        out = base + delta
        return out.strftime(self.dt_fmt)


    def datex(self, expr: str) -> str:
        """
        Supports chaining:
          "<anchor> (+|-) <duration> (+|-) <duration> ..."

        Examples:
          "today - 30 days + 2 weeks"
          "month start - 30 days + 2 weeks - 1 day"
          "last quarter end + 30 days - 1 week"
          "2026-01-01 - 30 days + 12 hours"
        """
        if not expr or not isinstance(expr, str):
            raise ValueError("expr must be a non-empty string")

        s = expr.strip()

        # If expression has no + or - operators at all => just resolve anchor/date
        if not re.search(r"[+-]", s):
            return self._resolve_anchor_to_date_str(s)

        # Find first operator (+ or -) that starts the arithmetic part.
        # Everything before that is the anchor.
        m0 = re.search(r"\s[+-]\s", re.sub(r"\s+", " ", s))
        if not m0:
            # could be just an anchor like "today" or "2025-01-01"
            return self._resolve_anchor_to_date_str(s)

        # Anchor is up to first operator occurrence in the ORIGINAL string.
        # We'll compute the cut point by searching in the original using a more flexible regex.
        m_anchor = re.search(r"\s*([+-])\s*", s)
        if not m_anchor:
            return self._resolve_anchor_to_date_str(s)

        anchor_part = s[:m_anchor.start()].strip()
        rest = s[m_anchor.start():].strip()

        base_str = self._resolve_anchor_to_date_str(anchor_part)
        cur = datetime.strptime(base_str, self.dt_fmt)  # midnight

        # Parse repeated segments: <op> <number> <unit>
        # Accept: "+ 30 days", "-30days", "+2 weeks", "- 1 day", etc.
        token_re = re.compile(r"""
            \s*([+-])\s*                           # operator
            ([+-]?\d+(?:\.\d+)?)\s*                # number
            ([a-zA-Z]+)                            # unit
        """, re.VERBOSE)

        pos = 0
        while pos < len(rest):
            m = token_re.match(rest, pos)
            if not m:
                raise ValueError(
                    f"Could not parse at: {rest[pos:]!r}. "
                    f"Expected something like '+ 30 days' or '-2 weeks'."
                )

            op = m.group(1)
            qty = m.group(2)
            unit = m.group(3).lower()

            delta = self._parse_duration_to_timedelta(f"{qty} {unit}")
            cur = cur + delta if op == "+" else cur - delta

            pos = m.end()

        return cur.strftime(self.dt_fmt)




    def to_dt(self, datestr):
        return datetime.strptime(datestr, dt_fmt).date()

    def now(self):
        if self.is_utc:
            today = (datetime.now() + timedelta(hours=5.5)).strftime(self.dtm_fmt)
        else:
            today = (datetime.now()).strftime(self.dtm_fmt)

        return today


    def dateminusduration(self, input_date, duration_string):
        '''
        input_date is a string like 2025-01-01
        duration_string is a string like 30 days, 2 weeks, 1 week, 1 day, 10 days, 5 hours, 5 hrs, 40 mins, 40 minutes, 10 secs, 1 sec, 1 min, 1 minute etc.
        '''
        if self.is_utc:
            result = (datetime.now() - timedelta(days=1) + timedelta(hours=5.5)).strftime(self.dt_fmt)
        else:
            result = (datetime.now() - timedelta(days=1)).strftime(self.dt_fmt)

        return result

    def yesterday(self):
        if self.is_utc:
            yesterday = (datetime.now() - timedelta(days=1) + timedelta(hours=5.5)).strftime(self.dt_fmt)
        else:
            yesterday = (datetime.now() - timedelta(days=1)).strftime(self.dt_fmt)

        return yesterday

    def today(self):
        if self.is_utc:
            today = (datetime.now() + timedelta(hours=5.5)).strftime(self.dt_fmt)
        else:
            today = (datetime.now()).strftime(self.dt_fmt)
        return today

    def today_x(self, x):
        if self.is_utc:
            today = (datetime.now() - timedelta(days=x) + timedelta(hours=5.5)).strftime(self.dt_fmt)
        else:
            today = (datetime.now() - timedelta(days=x)).strftime(self.dt_fmt)

        return today

    def today_7(self):
        today = self.today_x(7)
        return today

    def today_14(self):
        today = self.today_x(14)
        return today

    def today_21(self):
        today = self.today_x(21)
        return today

    def today_28(self):
        today = self.today_x(28)
        return today

    def week(self):
        return self.fn_week_tuple(self.today())

    def week_x(self, x):
        any_day_of_x_week = self.today_x(x*7)
        return self.fn_week_tuple(any_day_of_x_week)

    def current_week(self):
        return self.week()

    def last_week(self):
        return self.week_x(1)

    def previous_week(self):
        return self.week_x(1)

    def week_1(self):
        return self.week_x(1)

    def week_2(self):
        return self.week_x(2)

    def week_3(self):
        return self.week_x(3)

    def week_4(self):
        return self.week_x(4)

    def month(self):
        return (self.fn_first_day_of_month(self.today()), self.fn_last_day_of_month(self.today()))

    def month_x(self, x):
        first_day_of_month = self.fn_first_day_of_month(self.today())
        for i in np.arange(1, x+1):
            last_day_of_prev_month = (datetime.strptime(first_day_of_month, self.dt_fmt) - timedelta(days=1)).strftime(self.dt_fmt)
            first_day_of_month = self.fn_first_day_of_month(last_day_of_prev_month)
        last_day_of_month = self.fn_last_day_of_month(first_day_of_month)
        return (first_day_of_month, last_day_of_month)

    def now_datetime(self):
        if self.is_utc:
            today = (datetime.now() + timedelta(hours=5.5))
        else:
            today = (datetime.now())
        return today

    def yesterday_datetime(self):
        if self.is_utc:
            yesterday = (datetime.now() - timedelta(days=1) + timedelta(hours=5.5))
        else:
            yesterday = (datetime.now() - timedelta(days=1))
        return yesterday

    def today_datetime(self):
        if self.is_utc:
            today = (datetime.now() + timedelta(hours=5.5))
        else:
            today = (datetime.now())
        return today

    def today_x_datetime(self, x):
        if self.is_utc:
            today = (datetime.now() - timedelta(days=x) + timedelta(hours=5.5))
        else:
            today = (datetime.now() - timedelta(days=x))

        return today

    def today_7_datetime(self):
        today = self.today_x_datetime(7)
        return today

    def today_14__datetime(self):
        today = self.today_x_datetime(14)
        return today

    def today_21_datetime(self):
        today = self.today_x_datetime(21)
        return today

    def today_28_datetime(self):
        today = self.today_x_datetime(28)
        return today

    def week_datetime(self):
        return self.fn_week_tuple_datetime(self.today())

    def week_x_datetime(self, x):
        any_day_of_x_week = self.today_x(x*7)
        return self.fn_week_tuple_datetime(any_day_of_x_week)

    def current_week_datetime(self):
        return self.week_datetime()

    def last_week_datetime(self):
        return self.week_x_datetime(1)

    def previous_week_datetime(self):
        return self.week_x_datetime(1)

    def week_1_datetime(self):
        return self.week_x_datetime(1)

    def week_2_datetime(self):
        return self.week_x_datetime(2)

    def week_3_datetime(self):
        return self.week_x_datetime(3)

    def week_4_datetime(self):
        return self.week_x_datetime(4)

    def month(self):
        return (self.fn_first_day_of_month(self.today()), self.fn_last_day_of_month(self.today()))

    def month_x(self, x):
        first_day_of_month = self.fn_first_day_of_month(self.today())
        for i in np.arange(1, x+1):
            last_day_of_prev_month = (datetime.strptime(first_day_of_month, self.dt_fmt) - timedelta(days=1)).strftime(self.dt_fmt)
            first_day_of_month = self.fn_first_day_of_month(last_day_of_prev_month)
        last_day_of_month = self.fn_last_day_of_month(first_day_of_month)
        return (first_day_of_month, last_day_of_month)



    def current_month(self):
        return self.month()

    def last_month(self):
        return self.month_x(1)

    def previous_month(self):
        return self.month_x(1)

    def month_1(self):
        return self.month_x(1)

    def month_2(self):
        return self.month_x(2)

    def month_3(self):
        return self.month_x(3)

    def month_4(self):
        return self.month_x(4)

    def fn_week_tuple(self, datestr):
        '''
        Gives start date and end of monday to sunday week basis string input
        example. 2022-04-19 will give you output as ('2022-04-18', '2022-04-24')
        '''
        dt = datetime.strptime(datestr, self.dt_fmt)
        start = dt - timedelta(days=dt.weekday())
        end = start + timedelta(days=6)
        return (start.strftime(self.dt_fmt), end.strftime(self.dt_fmt))

    def fn_week_tuple_datetime(self, datestr):
        '''
        Gives start date and end of monday to sunday week basis string input
        example. 2022-04-19 will give you output as ('2022-04-18', '2022-04-24')
        '''
        dt = datetime.strptime(datestr, self.dt_fmt)
        start = dt - timedelta(days=dt.weekday())
        end = start + timedelta(days=6)
        return (start, end)

    def fn_last_day_of_month(self, datestr):
        # this will never fail
        # get close to the end of the month for any day, and add 4 days 'over'
        any_day = datetime.strptime(datestr, self.dt_fmt)
        next_month = any_day.replace(day=28) + timedelta(days=4)
        # subtract the number of remaining 'overage' days to get last day of current month, or said programattically said, the previous day of the first of next month
        return (next_month - timedelta(days=next_month.day)).strftime(self.dt_fmt)

    def fn_first_day_of_month(self, datestr):
        any_day = datetime.strptime(datestr, self.dt_fmt)
        return any_day.replace(day=1).strftime(self.dt_fmt)

    def date_split(self, start, end, intv):
        def date_range_generator(start, end, intv):
            start = datetime.strptime(start, self.dt_fmt)
            end = datetime.strptime(end, self.dt_fmt)
            diff = (end - start) / intv
            for i in range(intv):
                if(i != 0):
                    x = ((start + diff * i) - timedelta(days=1)).strftime(self.dt_fmt)
                    yield x
                x = (start + diff * i).strftime(self.dt_fmt)
                yield x
            yield end.strftime(self.dt_fmt)
        dt_lst = list(date_range_generator(start, end, intv))
        return list(zip(dt_lst[::2], dt_lst[1::2]))

    def date_split_extended(self, start_date, end_date, interval_type, dt_fmt="%Y-%m-%d"):
        """
        Splits the period from start_date to end_date into intervals by calendar period.
        Parameters:
            start_date (str): Start date in dt_fmt (default "%Y-%m-%d")
            end_date (str): End date in dt_fmt (default "%Y-%m-%d")
            interval_type (str): One of "day", "fortnight", "week", "month", "quarter", "year".
            dt_fmt (str): Date format string.
        Returns:
            List of tuples of strings [(interval_start, interval_end), ...].
        """
        # Convert input strings to date objects
        start = datetime.strptime(start_date, dt_fmt).date()
        end   = datetime.strptime(end_date, dt_fmt).date()
        intervals = []
        current = start

        while current <= end:
            it = interval_type.lower()
            if it == 'day':
                period_end = current
            elif it == 'fortnight':
                # 14-day windows
                period_end = current + timedelta(days=13)
            elif it == 'week':
                # Define a week as Monday to Sunday.
                days_to_sunday = 6 - current.weekday()
                period_end = current + timedelta(days=days_to_sunday)
            elif it == 'month':
                # Get last day of current month
                last_day = calendar.monthrange(current.year, current.month)[1]
                period_end = current.replace(day=last_day)
            elif it == 'quarter':
                # Quarters: Q1: Jan-Mar, Q2: Apr-Jun, Q3: Jul-Sep, Q4: Oct-Dec
                if current.month <= 3:
                    period_end = date(current.year, 3, 31)
                elif current.month <= 6:
                    period_end = date(current.year, 6, 30)
                elif current.month <= 9:
                    period_end = date(current.year, 9, 30)
                else:
                    period_end = date(current.year, 12, 31)
            elif it == 'year':
                period_end = date(current.year, 12, 31)
            else:
                raise ValueError(f"Unsupported interval type: {interval_type}")

            # Make sure not to go past the overall end date
            if period_end > end:
                period_end = end

            # Append the interval as formatted strings
            intervals.append((current.strftime(dt_fmt), period_end.strftime(dt_fmt)))

            # Next interval starts the day after period_end
            current = period_end + timedelta(days=1)

        return intervals

    def datetime_split(self, start, end, intv):
        def date_range_generator(start, end, intv):
            start = datetime.strptime(start, self.dtm_fmt)
            end = datetime.strptime(end, self.dtm_fmt)
            diff = (end - start) / intv
            for i in range(intv):
                if(i != 0):
                    x = ((start + diff * i) - timedelta(seconds=1)).strftime(self.dtm_fmt)
                    yield x
                x = (start + diff * i).strftime(self.dtm_fmt)
                yield x
            yield end.strftime(self.dtm_fmt)
        dt_lst = list(date_range_generator(start, end, intv))
        return list(zip(dt_lst[::2], dt_lst[1::2]))
