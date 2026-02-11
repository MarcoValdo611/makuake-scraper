"""
Railway 要求每个 Python 项目有一个可启动的入口。
本文件提供一个最小的占位进程，方便部署和查看日志。

你的真实业务逻辑依然通过：
- `python -m scraper.jobs run_hourly`
- `python -m scraper.jobs compute_daily`
由 Railway 的定时任务（Cron）来调用。
"""

import logging
import time


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main() -> None:
    logger.info("Makuake scraper worker is running (idle). Waiting for cron jobs...")
    # 保持进程存活，方便 Railway 认为服务是“running”
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        logger.info("Shutting down.")


if __name__ == "__main__":
    main()

