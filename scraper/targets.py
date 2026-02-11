import csv
from datetime import date
from dataclasses import dataclass
from pathlib import Path

# 自动定位项目根目录下的 targets.csv
# parent是scraper文件夹，parent.parent是项目根目录
TARGET_CSV_PATH = Path(__file__).resolve().parent.parent / "targets.csv"

@dataclass
class DailyTarget:
    date: date
    goal_daily_amount: int
    goal_daily_quantity: int
    goal_total_amount: int
    goal_total_quantity: int

def get_target_for_date(d: date) -> DailyTarget | None:
    if not TARGET_CSV_PATH.exists():
        return None

    with open(TARGET_CSV_PATH, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                row_date = date.fromisoformat(row["date"].strip())
                if row_date == d:
                    return DailyTarget(
                        date=row_date,
                        goal_daily_amount=int(row["goal_daily_amount"]),
                        goal_daily_quantity=int(row["goal_daily_quantity"]),
                        goal_total_amount=int(row["goal_total_amount"]),
                        goal_total_quantity=int(row["goal_total_quantity"]),
                    )
            except (ValueError, KeyError):
                continue
    return None