"""Removes emojis from app.py (keeps the browser-tab icon). Run:  python strip_emoji.py"""
import re, shutil
EMOJI = re.compile("[\U0001F000-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF\u2300-\u23FF\uFE0F\u200D]+ ?")
shutil.copy("app.py", "app_backup.py")
out = []
for line in open("app.py", encoding="utf-8"):
    if "page_icon" not in line:
        line = line.replace("{ACTION_ICON[a]} ", "").replace("{e} ", "")
        line = EMOJI.sub("", line)
    out.append(line)
open("app.py", "w", encoding="utf-8").write("".join(out))
print("Done. Backup saved as app_backup.py")