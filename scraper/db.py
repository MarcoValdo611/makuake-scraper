from __future__ import annotations

import contextlib
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable, Optional

import psycopg2
from psycopg2.extras import RealDictCursor

from .config import settings


@dataclass
class SnapshotRow:
    id: int
    scraped_at: datetime  # UTC
    total_amount: int
    total_quantity: int


def get_conn():
    if not settings.database_url:
        raise RuntimeError("DATABASE_URL is not set.")
    return psycopg2.connect(settings.database_url)


def create_tables():
    with get_conn() as conn:
        with conn.cursor() as cur:
            # 1. 创建原始快照表
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS raw_snapshots (
                    id SERIAL PRIMARY KEY,
                    scraped_at TIMESTAMPTZ NOT NULL,
                    total_amount BIGINT NOT NULL,
                    total_quantity INTEGER NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                """
            )
            
            # 2. 创建每日统计表 (包含所有新字段)
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS daily_metrics (
                    date DATE PRIMARY KEY,
                    
                    -- 实际数据
                    baseline_amount BIGINT NOT NULL,
                    baseline_quantity INTEGER NOT NULL,
                    end_amount BIGINT NOT NULL,
                    end_quantity INTEGER NOT NULL,
                    
                    -- 目标数据 (新增)
                    goal_daily_amount BIGINT DEFAULT 0,
                    goal_daily_quantity INTEGER DEFAULT 0,
                    goal_total_amount BIGINT DEFAULT 0,
                    goal_total_quantity INTEGER DEFAULT 0,
                    
                    -- 差异数据 (新增)
                    diff_daily_amount BIGINT DEFAULT 0,
                    diff_daily_quantity INTEGER DEFAULT 0,
                    diff_total_amount BIGINT DEFAULT 0,
                    diff_total_quantity INTEGER DEFAULT 0,
                    
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                """
            )

def insert_snapshot(total_amount: int, total_quantity: int, scraped_at: Optional[datetime] = None) -> None:
    if scraped_at is None:
        scraped_at = datetime.now(timezone.utc)

    with contextlib.closing(get_conn()) as conn, conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO raw_snapshots (scraped_at, total_amount, total_quantity)
            VALUES (%s, %s, %s);
            """,
            (scraped_at, total_amount, total_quantity),
        )


def get_snapshots_between(start: datetime, end: datetime) -> list[SnapshotRow]:
    with contextlib.closing(get_conn()) as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """
            SELECT id, scraped_at, total_amount, total_quantity
            FROM raw_snapshots
            WHERE scraped_at >= %s AND scraped_at < %s
            ORDER BY scraped_at ASC;
            """,
            (start, end),
        )
        rows = cur.fetchall()
    return [
        SnapshotRow(
            id=row["id"],
            scraped_at=row["scraped_at"],
            total_amount=row["total_amount"],
            total_quantity=row["total_quantity"],
        )
        for row in rows
    ]


def get_last_snapshot_before(when: datetime) -> Optional[SnapshotRow]:
    with contextlib.closing(get_conn()) as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """
            SELECT id, scraped_at, total_amount, total_quantity
            FROM raw_snapshots
            WHERE scraped_at <= %s
            ORDER BY scraped_at DESC
            LIMIT 1;
            """,
            (when,),
        )
        row = cur.fetchone()
    if not row:
        return None
    return SnapshotRow(
        id=row["id"],
        scraped_at=row["scraped_at"],
        total_amount=row["total_amount"],
        total_quantity=row["total_quantity"],
    )


def upsert_daily_metrics(
    date,
    baseline_amount, baseline_quantity,
    end_amount, end_quantity,
    goal_daily_amount=0, goal_daily_quantity=0,
    goal_total_amount=0, goal_total_quantity=0,
    diff_daily_amount=0, diff_daily_quantity=0,
    diff_total_amount=0, diff_total_quantity=0,
):
    # 1. 在 Python 层面计算出老字段的值，防止数据库报错
    # 逻辑：今日新增 = 今日最终 - 昨日基准
    calc_sales_amount_today = end_amount - baseline_amount
    calc_sales_quantity_today = end_quantity - baseline_quantity

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO daily_metrics (
                    date, 
                    baseline_amount, baseline_quantity,
                    end_amount, end_quantity,
                    
                    -- 🔴 必须显式插入这两个老字段 (Not Null)
                    sales_amount_today, sales_quantity_today,
                    
                    -- 新增字段
                    goal_daily_amount, goal_daily_quantity,
                    goal_total_amount, goal_total_quantity,
                    diff_daily_amount, diff_daily_quantity,
                    diff_total_amount, diff_total_quantity,
                    updated_at
                )
                VALUES (
                    %s, 
                    %s, %s, 
                    %s, %s, 
                    
                    -- 🔴 插入计算出的值
                    %s, %s, 
                    
                    %s, %s, %s, %s, %s, %s, %s, %s,
                    NOW()
                )
                ON CONFLICT (date) DO UPDATE SET
                    baseline_amount = EXCLUDED.baseline_amount,
                    baseline_quantity = EXCLUDED.baseline_quantity,
                    end_amount = EXCLUDED.end_amount,
                    end_quantity = EXCLUDED.end_quantity,
                    
                    -- 🔴 更新时也要带上它们
                    sales_amount_today = EXCLUDED.sales_amount_today,
                    sales_quantity_today = EXCLUDED.sales_quantity_today,
                    
                    goal_daily_amount = EXCLUDED.goal_daily_amount,
                    goal_daily_quantity = EXCLUDED.goal_daily_quantity,
                    goal_total_amount = EXCLUDED.goal_total_amount,
                    goal_total_quantity = EXCLUDED.goal_total_quantity,
                    diff_daily_amount = EXCLUDED.diff_daily_amount,
                    diff_daily_quantity = EXCLUDED.diff_daily_quantity,
                    diff_total_amount = EXCLUDED.diff_total_amount,
                    diff_total_quantity = EXCLUDED.diff_total_quantity,
                    updated_at = NOW();
                """,
                (
                    date,
                    baseline_amount, baseline_quantity,
                    end_amount, end_quantity,
                    
                    # 对应上面的 %s, %s (Calculated Sales)
                    calc_sales_amount_today, calc_sales_quantity_today,
                    
                    goal_daily_amount, goal_daily_quantity,
                    goal_total_amount, goal_total_quantity,
                    diff_daily_amount, diff_daily_quantity,
                    diff_total_amount, diff_total_quantity
                ),
            )
