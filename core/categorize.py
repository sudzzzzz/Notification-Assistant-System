"""Model 1: text -> category (TF-IDF + Logistic Regression) and a urgency score."""
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline, make_union

CATEGORIES = ["work", "family", "shopping", "college", "finance", "social"]

SEED = {
 "work": ["Can you send me the document today?", "Standup moved to 11, please join", "Please review the pull request before EOD",
          "Client wants the report by tomorrow", "Meeting invite: Sprint planning", "Your Jira ticket was assigned to you",
          "Deployment failed on production", "Can we sync on the project deadline?", "New email from your manager",
          "Slack: @you can you check the build?"],
 "family": ["Mom: call me when you are free", "Dad: did you reach home?", "Dinner at 8 tonight, are you coming?",
            "Bhai: send me the photos", "Mom: don't forget to eat", "Sis: happy birthday party planning",
            "Family group: Sunday lunch at nani's", "Papa: pick me up at the station", "Mom: are you ok?"],
 "shopping": ["50% off sale ends tonight", "Your order has been shipped", "Flash deal: buy 1 get 1 free",
              "Your cart is waiting, complete your purchase", "Out for delivery today", "Exclusive coupon just for you",
              "Big billion days start now", "Rate your recent purchase", "New arrivals you may like"],
 "college": ["Assignment 3 submission deadline extended", "Lab viva scheduled tomorrow morning", "Internal exam timetable released",
             "Placement drive registration open", "Attendance below 75 percent warning", "Professor uploaded new lecture notes",
             "Module 5 project submission reminder", "College fee due notice", "Campus recruitment test link"],
 "finance": ["Rs 2,500 debited from your account", "Your credit card bill is due in 3 days", "UPI payment received",
             "OTP for your transaction is 482913", "EMI due tomorrow", "Your salary has been credited",
             "Low balance alert", "Bank statement is ready", "Payment failed, please retry"],
 "social": ["Rahul liked your photo", "You have 5 new followers", "Someone commented on your post",
            "Your friend posted a new story", "Group chat: who is up for movie?", "Tagged you in a photo",
            "New reel from your friend", "Trending near you", "Rohan sent you a friend request"],
}

_URGENT = re.compile(r"\b(today|urgent|asap|now|immediately|eod|deadline|due|tonight|expires?|ends?|failed|"
                     r"important|critical|last day|reminder|are you ok|call me)\b", re.I)

def urgency_score(text: str) -> float:
    hits = len(_URGENT.findall(text))
    q = 0.15 if "?" in text else 0.0
    return round(min(1.0, 0.35 * hits + q), 2)

class Categorizer:
    def __init__(self):
        X, y = [], []
        for cat, texts in SEED.items():
            X += texts; y += [cat] * len(texts)
        feats = make_union(TfidfVectorizer(ngram_range=(1, 2), lowercase=True),
                           TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5)))
        self.model = make_pipeline(feats, LogisticRegression(max_iter=1000, C=5))
        self.model.fit(X, y)

    def predict(self, text: str):
        proba = self.model.predict_proba([text])[0]
        i = proba.argmax()
        return self.model.classes_[i], float(proba[i])
