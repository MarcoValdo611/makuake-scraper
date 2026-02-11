from __future__ import annotations

import logging
import sys

# 务必确保引入了 finalize_today_metrics
from .logic import finalize_today_metrics, scrape_once


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_hourly() -> None:
    """
    每小时由 Railway 定时任务调用：
    1. 抓取最新数据快照
    2. 立即计算并更新今日的累计销量
    """
    try:
        # 第一步：抓取原始数据
        metrics = scrape_once()
        logger.info(
            "Scraped snapshot: total_amount=%s, total_quantity=%s",
            metrics.total_amount,
            metrics.total_quantity,
        )

        # 第二步：立即计算今日增量并存入数据库 (实时更新今日战况)
        daily = finalize_today_metrics()
        if daily:
            logger.info(
                "Updated daily metrics: Sales Today=%s, Amount Today=%s",
                daily.sales_quantity_today,
                daily.sales_amount_today
            )

    except Exception as exc:  # noqa: BLE001
        logger.exception("run_hourly failed: %s", exc)
        raise


def compute_daily() -> None:
    """
    每天 23:15 由 Railway 定时任务调用：
    作为每日最终结算的双保险
    """
    try:
        metrics = finalize_today_metrics()
        if metrics is None:
            logger.warning("compute_daily: not enough data to compute today metrics.")
            return
        logger.info(
            "Daily metrics (Finalized): sales_amount_today=%s, sales_quantity_today=%s",
            metrics.sales_amount_today,
            metrics.sales_quantity_today,
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("compute_daily failed: %s", exc)
        raise


if __name__ == "__main__":
    # 命令行入口逻辑
    if len(sys.argv) < 2:
        print("Usage: python -m scraper.jobs [run_hourly|compute_daily]")
        raise SystemExit(1)

    cmd = sys.argv[1]
    if cmd == "run_hourly":
        run_hourly()
    elif cmd == "compute_daily":
        compute_daily()
    else:
        print(f"Unknown command: {cmd}")
        raise SystemExit(1)
