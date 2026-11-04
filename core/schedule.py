"""Turn an action label into a concrete reminder time."""
from datetime import datetime, timedelta

ACTIONS = ["1h", "tonight", "tomorrow", "important", "ignore"]
LABELS = {"1h": "In 1 hour", "tonight": "Tonight", "tomorrow": "Tomorrow morning",
          "important": "Mark important", "ignore": "Ignore"}

def due_time(action: str, now: datetime):
    if action == "1h":
        return now + timedelta(hours=1)
    if action == "tonight":
        t = now.replace(hour=20, minute=0, second=0, microsecond=0)
        return t if t > now + timedelta(minutes=30) else now + timedelta(hours=1)
    if action == "tomorrow":
        return (now + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
    if action == "important":
        return now + timedelta(hours=3)   # important items resurface in 3h
    return None  # ignore -> no reminder
