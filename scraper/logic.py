from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, time, timedelta, timezone
import pytz

from .config import settings
from .db import (
    SnapshotRow, 
    get_last_snapshot_before, 
    upsert_daily_metrics, 
    insert_snapshot  # 必须导入这个
)
from .fetcher import fetch_page
from .parser import SnapshotMetrics, parse_metrics
from .targets import get_target_for_date

tz_local = pytz.timezone(settings.timezone)

@dataclass
class TodayMetrics:
    now_at: datetime
    # 实际数据
    sales_amount_today: int
    sales_quantity_today: int
    total_amount: int
    total_quantity: int
    # 目标数据
    goal_daily_amount: int
    goal_daily_quantity: int
    goal_total_amount: int
    goal_total_quantity: int
    # 差异与进度 (计算结果)
    gap_daily_amount: int
    gap_daily_quantity: int
    gap_total_amount: int
    gap_total_quantity: int
    pct_daily_amount: float
    pct_daily_quantity: float
    pct_total_amount: float
    pct_total_quantity: float


def scrape_once() -> SnapshotMetrics:
    """
    抓取一次页面并存入 raw_snapshots 表。
    这是最基础的爬虫功能。
    """
    html_text = fetch_page()
    metrics = parse_metrics(html_text)
    insert_snapshot(total_amount=metrics.total_amount, total_quantity=metrics.total_quantity)
    return metrics


def finalize_today_metrics(now_utc: datetime | None = None) -> TodayMetrics | None:
    """
    计算今日数据，对比目标，并更新 daily_metrics 表。
    """
    if now_utc is None:
        now_utc = datetime.now(timezone.utc)

    # 1. 基础数据计算
    now_local = now_utc.astimezone(tz_local)
    today_local_date = now_local.date()
    
    yesterday_local_date = today_local_date - timedelta(days=1)
    baseline_local_dt = tz_local.localize(datetime.combine(yesterday_local_date, time(23, 0, 0)))
    baseline_utc = baseline_local_dt.astimezone(timezone.utc)

    baseline_snapshot = get_last_snapshot_before(baseline_utc)
    latest_snapshot = get_last_snapshot_before(now_utc)

    if not baseline_snapshot or not latest_snapshot:
        return None

    actual_daily_amt = latest_snapshot.total_amount - baseline_snapshot.total_amount
    actual_daily_qty = latest_snapshot.total_quantity - baseline_snapshot.total_quantity
    actual_total_amt = latest_snapshot.total_amount
    actual_total_qty = latest_snapshot.total_quantity

    # 2. 读取目标
    target = get_target_for_date(today_local_date)
    
    # 默认目标为0，防止报错
    g_d_amt = target.goal_daily_amount if target else 0
    g_d_qty = target.goal_daily_quantity if target else 0
    g_t_amt = target.goal_total_amount if target else 0
    g_t_qty = target.goal_total_quantity if target else 0

    # 3. 计算GAP (Gap = 目标 - 实际，如果是正数说明还差多少，负数说明超额)
    gap_d_amt = g_d_amt - actual_daily_amt
    gap_d_qty = g_d_qty - actual_daily_qty
    gap_t_amt = g_t_amt - actual_total_amt
    gap_t_qty = g_t_qty - actual_total_qty

    # 4. 计算百分比
    def calc_pct(actual, goal):
        return (actual / goal * 100) if goal > 0 else 0.0

    metrics = TodayMetrics(
        now_at=latest_snapshot.scraped_at.astimezone(tz_local),
        sales_amount_today=actual_daily_amt,
        sales_quantity_today=actual_daily_qty,
        total_amount=actual_total_amt,
        total_quantity=actual_total_qty,
        goal_daily_amount=g_d_amt,
        goal_daily_quantity=g_d_qty,
        goal_total_amount=g_t_amt,
        goal_total_quantity=g_t_qty,
        gap_daily_amount=gap_d_amt,
        gap_daily_quantity=gap_d_qty,
        gap_total_amount=gap_t_amt,
        gap_total_quantity=gap_t_qty,
        pct_daily_amount=calc_pct(actual_daily_amt, g_d_amt),
        pct_daily_quantity=calc_pct(actual_daily_qty, g_d_qty),
        pct_total_amount=calc_pct(actual_total_amt, g_t_amt),
        pct_total_quantity=calc_pct(actual_total_qty, g_t_qty),
    )

    # 5. 存入数据库
    upsert_daily_metrics(
        date=today_local_date,
        baseline_amount=baseline_snapshot.total_amount,
        baseline_quantity=baseline_snapshot.total_quantity,
        end_amount=latest_snapshot.total_amount,
        end_quantity=latest_snapshot.total_quantity,
        goal_daily_amount=g_d_amt,
        goal_daily_quantity=g_d_qty,
        goal_total_amount=g_t_amt,
        goal_total_quantity=g_t_qty,
        diff_daily_amount=gap_d_amt,
        diff_daily_quantity=gap_d_qty,
        diff_total_amount=gap_t_amt,
        diff_total_quantity=gap_t_qty,
    )

    return metrics
