import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import SessionLocal
from app.models import WeeklyProduction, MonthlyProduction

if __name__ == '__main__':
    db = SessionLocal()
    try:
        w = db.query(WeeklyProduction).count()
        m = db.query(MonthlyProduction).count()
        print(f"WEEKLY_COUNT={w}")
        print(f"MONTHLY_COUNT={m}")
    finally:
        db.close()
