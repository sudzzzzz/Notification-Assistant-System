"""Headless demo: simulates a user and prints how recommendation accuracy improves.
Run:  python run_demo.py"""
import random, os, tempfile
import pandas as pd
from core import db
from core.categorize import Categorizer, urgency_score
from core.recommend import Recommender
from core.simulator import random_notification, persona_action, random_time

random.seed(1)
c = db.conn(os.path.join(tempfile.mkdtemp(), "demo.db"))
cat_model, rec = Categorizer(), Recommender()
hits, window = [], 25
print(f"{'#':>4} {'trained on':>10} {'accuracy (last 25)':>20}  model state")
for i in range(1, 201):
    true_cat, app, text = random_notification()
    cat, conf = cat_model.predict(text)
    urg, ts = urgency_score(text), random_time()
    probs, state = rec.predict(cat, app, urg, ts)
    guess = rec.best(probs)
    truth = persona_action(true_cat, ts.hour, urg)
    hits.append(guess == truth)
    nid = db.add_notification(c, app, "demo", text, cat, urg, ts)
    db.log_choice(c, nid, cat, app, ts, urg, truth, "user")
    if i % 10 == 0:
        rec.fit(db.user_choices_df(c))
    if i % 25 == 0:
        print(f"{i:>4} {rec.n:>10} {sum(hits[-window:])/window:>19.0%}  {state}")
