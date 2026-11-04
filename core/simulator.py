"""Fake notifications + a fake 'user persona' so you can watch the model learn."""
import random
from datetime import datetime, timedelta
from .categorize import SEED, urgency_score

APPS = {"work": ["Slack", "Gmail", "Teams"], "family": ["WhatsApp"], "shopping": ["Amazon", "Flipkart"],
        "college": ["Gmail", "Classroom"], "finance": ["GPay", "Bank"], "social": ["Instagram", "Snapchat"]}

def random_notification():
    cat = random.choice(list(SEED))
    return cat, random.choice(APPS[cat]), random.choice(SEED[cat])

def persona_action(cat, hour, urgency, rng=random):
    """Hidden habits we want the model to discover. 10% noise = real humans are inconsistent."""
    if rng.random() < 0.10:
        return rng.choice(["1h", "tonight", "tomorrow", "important", "ignore"])
    if cat == "family":   return "1h"
    if cat == "shopping": return "ignore"
    if cat == "social":   return "ignore" if hour < 18 else "tonight"
    if cat == "work":     return "1h" if urgency >= 0.6 else "tonight"
    if cat == "college":  return "tomorrow" if hour >= 16 else "1h"
    if cat == "finance":  return "important"
    return "tonight"

def random_time(days_back=14):
    base = datetime.now() - timedelta(days=random.randint(0, days_back))
    return base.replace(hour=random.randint(7, 23), minute=random.randint(0, 59))
