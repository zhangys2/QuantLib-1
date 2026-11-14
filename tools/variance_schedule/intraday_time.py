"""Five-minute UTC intervals and local variance-profile keys."""

from datetime import timedelta, timezone


UTC = timezone.utc
FIVE_MINUTES = timedelta(minutes=5)


def floor_slot(timestamp):
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise ValueError("timestamps require a timezone")
    timestamp = timestamp.astimezone(UTC)
    return timestamp.replace(second=0, microsecond=0) - timedelta(minutes=timestamp.minute % 5)


def slot_key(slot_start, local_timezone, day_category):
    local = slot_start.astimezone(local_timezone)
    if local.minute % 5 or local.second or local.microsecond:
        raise ValueError("local timezone offset must align with five-minute slots")
    return day_category(local.date()), local.hour * 60 + local.minute


def intervals(start, end):
    if (start.tzinfo is None or start.utcoffset() is None
            or end.tzinfo is None or end.utcoffset() is None):
        raise ValueError("interval boundaries require a timezone")
    current, end = start.astimezone(UTC), end.astimezone(UTC)
    while current < end:
        slot_start = floor_slot(current)
        stop = min(end, slot_start + FIVE_MINUTES)
        yield slot_start, current, stop
        current = stop
