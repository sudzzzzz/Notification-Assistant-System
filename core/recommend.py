"""Model 2: personalised 'when should I remind you?' recommender.

Cold start  : hand-written prior (rules).
Learning    : RandomForest trained on the user's OWN choices (source='user' only,
              so AI decisions never feed back into training).
Blending    : weight on the learned model grows with the amount of data.
"""
import numpy as np, pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from .schedule import ACTIONS

MIN_SAMPLES = 12      # below this we only use the prior
FULL_TRUST = 60       # at this many samples the model gets weight 1.0

def prior(category, urgency, hour):
    p = {a: 0.05 for a in ACTIONS}
    if category == "family":      p["1h"] += 0.6
    elif category == "work":      p["tonight" if hour < 17 else "tomorrow"] += 0.55; p["important"] += 0.15
    elif category == "college":   p["tomorrow"] += 0.5; p["important"] += 0.2
    elif category == "finance":   p["important"] += 0.4; p["tonight"] += 0.2
    elif category == "shopping":  p["ignore"] += 0.7
    elif category == "social":    p["ignore"] += 0.4; p["tonight"] += 0.2
    if urgency >= 0.6:            p["1h"] += 0.4; p["important"] += 0.2
    s = sum(p.values())
    return {a: v / s for a, v in p.items()}

def _frame(rows):
    df = pd.DataFrame(rows)
    df["hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24)
    df["hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24)
    return df[["category", "app", "hour_sin", "hour_cos", "weekend", "urgency"]]

class Recommender:
    def __init__(self):
        self.pipe, self.n = None, 0

    def fit(self, df):
        """df = user choices (columns: category, app, hour, weekend, urgency, action)."""
        self.n = len(df)
        if self.n < MIN_SAMPLES or df["action"].nunique() < 2:
            self.pipe = None
            return self
        pre = ColumnTransformer([("oh", OneHotEncoder(handle_unknown="ignore"), ["category", "app"])],
                                remainder="passthrough")
        self.pipe = Pipeline([("pre", pre),
                              ("rf", RandomForestClassifier(n_estimators=200, min_samples_leaf=2, random_state=0))])
        self.pipe.fit(_frame(df.to_dict("records")), df["action"])
        return self

    @property
    def trust(self):
        if self.pipe is None: return 0.0
        return min(1.0, self.n / FULL_TRUST)

    def predict(self, category, app, urgency, ts):
        pr = prior(category, urgency, ts.hour)
        if self.pipe is None:
            return pr, "prior"
        row = _frame([dict(category=category, app=app, hour=ts.hour, weekend=int(ts.weekday() >= 5), urgency=urgency)])
        raw = dict(zip(self.pipe.classes_, self.pipe.predict_proba(row)[0]))
        w = self.trust
        out = {a: w * raw.get(a, 0.0) + (1 - w) * pr[a] for a in ACTIONS}
        return out, f"learned ({self.n} choices, trust {w:.0%})"

    def best(self, probs):
        return max(probs, key=probs.get)
