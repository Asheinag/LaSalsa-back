import calendar
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

RUN_HOUR = 9
RUN_MINUTE = 0


def clamp_day_to_month(day: int, year: int, month: int) -> int:
    max_day = calendar.monthrange(year, month)[1]
    return min(day, max_day)


def calculate_next_run(
    frequency: str,
    days: list[int],
    user_timezone: str,
    from_dt: datetime,
) -> datetime:
    tz = ZoneInfo(user_timezone)
    now_local = from_dt.astimezone(tz)

    if frequency == "daily":
        next_local = (now_local + timedelta(days=1)).replace(
            hour=RUN_HOUR, minute=RUN_MINUTE, second=0, microsecond=0
        )

    elif frequency == "weekly":
        next_local = None
        for i in range(1, 8):
            candidate = now_local + timedelta(days=i)
            if candidate.weekday() in days:
                next_local = candidate.replace(
                    hour=RUN_HOUR, minute=RUN_MINUTE, second=0, microsecond=0
                )
                break
        if next_local is None:
            raise ValueError(f"Не удалось найти подходящий день недели: {days}")

    elif frequency == "monthly":
        next_local = None
        # смотрим текущий и следующие 2 месяца
        for month_offset in range(3):
            year = now_local.year
            month = now_local.month + month_offset
            if month > 12:
                month -= 12
                year += 1
            # дедуплицируем после clamp
            clamped_days = sorted(set(clamp_day_to_month(d, year, month) for d in days))
            for day in clamped_days:
                candidate = now_local.replace(
                    year=year,
                    month=month,
                    day=day,
                    hour=RUN_HOUR,
                    minute=RUN_MINUTE,
                    second=0,
                    microsecond=0,
                )
                if candidate > now_local:
                    next_local = candidate
                    break
            if next_local is not None:
                break
        if next_local is None:
            raise ValueError(f"Не удалось найти подходящий день месяца: {days}")

    elif frequency == "interval":
        interval_days = days[0] if days else 1
        next_local = (now_local + timedelta(days=interval_days)).replace(
            hour=RUN_HOUR, minute=RUN_MINUTE, second=0, microsecond=0
        )

    else:
        raise ValueError(f"Неизвестный тип расписания: {frequency}")

    return next_local.astimezone(ZoneInfo("UTC"))
