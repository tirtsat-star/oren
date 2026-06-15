#!/usr/bin/env python3
"""
הרץ: python3 update.py
מושך אזהרות חדשות מ-RASFF, מעדכן index.html, ודוחף לגיטהאב.
"""
import subprocess, sys
from pathlib import Path

HERE = Path(__file__).parent

def run(cmd):
    result = subprocess.run(cmd, shell=True, cwd=HERE, capture_output=True, text=True)
    if result.returncode != 0:
        print("שגיאה:", result.stderr)
        sys.exit(1)
    return result.stdout.strip()

print("1/3  מושך אזהרות חדשות מ-RASFF...")
result = subprocess.run([sys.executable, str(HERE / "refresh.py")], cwd=HERE)
if result.returncode != 0:
    print("שגיאה בריצת refresh.py")
    sys.exit(1)

print("2/3  מעלה לגיטהאב...")
run("git add index.html")
status = run("git diff --staged --name-only")
if not status:
    print("אין שינויים — האזהרות כבר מעודכנות.")
    sys.exit(0)

from datetime import datetime
date = datetime.utcnow().strftime("%d/%m/%Y")
run(f'git commit -m "עדכון אזהרות {date}"')
run("git push")

print("3/3  האתר עודכן!")
print("     https://tirtsat-star.github.io/oren/")
