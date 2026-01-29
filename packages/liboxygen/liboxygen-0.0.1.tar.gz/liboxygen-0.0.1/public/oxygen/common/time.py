from typing import Optional
from dateutil.relativedelta import relativedelta
import datetime
import time


# for allowing external references
Timedelta = datetime.timedelta
Relativedelta = relativedelta
Timezone = datetime.timezone
DateTime = datetime.datetime  # TODO: prevent other imports of datetime in unit tests and the use of "Date.now"
Date = datetime.date          # TODO: prevent other imports of datetime in unit tests and the use of "Date.now"


def infer_time(timelike) -> datetime.datetime:
    if isinstance(timelike, datetime.datetime):
        assert timelike.tzinfo == datetime.timezone.utc, f"Timezone must be utc everywhere!"
        return timelike
    attempts = [
        lambda timelike: datetime.datetime.fromtimestamp(int(timelike), tz=datetime.timezone.utc),
        lambda timelike: datetime.datetime.fromtimestamp(int(timelike)/1e6, tz=datetime.timezone.utc),
        lambda timelike: datetime.datetime.fromisoformat(timelike.split(".")[0])
    ]
    for attempt in attempts:
        try:
            return attempt(timelike)
        except:
            pass
    raise RuntimeError(f"Could not infer time from {timelike}")

def now() -> datetime.datetime:
    return datetime.datetime.now(tz=datetime.timezone.utc)

def timestamp() -> int:
    return int(now().timestamp())

def readable_timestamp() -> str:
    date_now = now()
    return date_now.strftime("%Y%m%d-%H%M%S")

def serialize_date(date: Date) -> str:
    return date.strftime("%Y-%m-%d")

def deserialize_date(date: str) -> Date:
    if isinstance(date, Date):
        return date
    return DateTime.strptime(date, "%Y-%m-%d").date()

