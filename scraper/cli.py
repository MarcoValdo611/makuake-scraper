from __future__ import annotations

import argparse
import logging
import sys

# 务必导入 finalize_today_metrics，因为它包含了读取 CSV 和计算 GAP 的逻辑
from .db import create_tables
from .logic import finalize_today_metrics, scrape_once


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def format_wan(value: int | float | None) -> str:
    """将金额转换为'万'单位，保留小数点后1位，如果是整数则不显示小数"""
    if value is None:
        return "0.0万"
    val_wan = value / 10000.0
    # 如果是整数（比如 100.00），显示 100万；否则显示 100.5万
    if val_wan.is_integer():
        return f"{int(val_wan)}万"
    return f"{val_wan:.1f}万"


def get_report_text() -> str:
    """
    核心逻辑：获取今日数据并生成格式化的文本战报。
    该函数返回字符串，既可以用于 print，也可以用于发送飞书消息。
    """
    try:
        metrics = finalize_today_metrics()
        
        if metrics is None:
            return "【数据不足】无法计算。请确保数据库中至少有昨天的基准数据和今天的最新数据。\n提示：如果是第一次运行，请手动去数据库修改一条历史数据的时间为昨天。"

        # --- 格式化时间 ---
        # 为了兼容性，统一使用 %m (02月) 而不是 %-m (2月)，防止在某些Linux环境报错
        dt_str = metrics.now_at.strftime("%m月%d日 %H:%M")

        lines = []
        # 1. 标题与实际数据
        lines.append(f"{dt_str} 战报")
        lines.append(f"新增人数: {metrics.sales_quantity_today} 人")
        lines.append(f"新增金额: {format_wan(metrics.sales_amount_today)}")
        lines.append("") # 空行

        # 2. 目标数据
        lines.append(f"目标人数: {metrics.goal_daily_quantity} 人")
        lines.append(f"目标金额: {format_wan(metrics.goal_daily_amount)}")
        lines.append("")

        # 3. 当日 GAP 与 进度
        lines.append(f"人数GAP: {metrics.gap_daily_quantity} (进度 {metrics.pct_daily_quantity:.1f}%)")
        lines.append(f"金额GAP: {format_wan(metrics.gap_daily_amount)} (进度 {metrics.pct_daily_amount:.1f}%)")
        lines.append("-" * 20)

        # 4. 累计 GAP 与 进度
        lines.append(f"累计人数GAP: {metrics.gap_total_quantity}")
        lines.append(f"累计金额GAP: {format_wan(metrics.gap_total_amount)}")
        
        return "\n".join(lines)

    except Exception as e:
        logger.error(f"Generate report failed: {e}")
        return f"❌ 生成战报时出错: {str(e)}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Makuake scraper CLI")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("init-db", help="Create database tables")
    sub.add_parser("scrape-once", help="Fetch page once and store snapshot")
    sub.add_parser("today-metrics", help="Calculate and print today's metrics with targets")

    args = parser.parse_args()

    if args.command == "init-db":
        create_tables()
        print("Tables created (if not exist).")

    elif args.command == "scrape-once":
        try:
            metrics = scrape_once()
            print(
                f"Scraped successfully:\n"
                f"Total Amount: {metrics.total_amount}\n"
                f"Total Quantity: {metrics.total_quantity}"
            )
        except Exception as e:
            logger.error(f"Scrape failed: {e}")
            sys.exit(1)

    elif args.command == "today-metrics":
        # 直接调用封装好的函数并打印
        print(get_report_text())

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
