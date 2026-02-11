import sys
from datetime import datetime, timedelta, timezone
# 确保能导入 scraper 模块
from scraper.db import get_conn

def seed():
    print("正在连接数据库并注入测试数据...")
    
    conn = get_conn()
    if conn is None:
        print("❌ 无法连接数据库，请检查 .env 文件配置")
        return

    # --- 1. 设定时间点 (非常关键) ---
    # 我们需要模拟 "昨天" 和 "今天" 的数据
    # 假设今天是 2月11日
    
    # 获取当前 UTC 时间
    now_utc = datetime.now(timezone.utc)
    
    # 构造 "今天" (模拟今天下午 14:00 抓取的数据)
    # 注意：这里我们动态获取今天的日期，保证你无论哪天跑这个脚本都是 "今天"
    today_snapshot = now_utc

    # 构造 "昨天" (模拟昨天晚上 23:00 的基准数据)
    yesterday_snapshot = now_utc - timedelta(days=1)
    # 强制把时间设为昨天的 14:00 UTC (即北京/东京时间的晚上)
    yesterday_snapshot = yesterday_snapshot.replace(hour=14, minute=0, second=0, microsecond=0)


    # --- 2. 设定数值 (凑答案) ---
    # 你的目标测试场景：
    # 新增人数 = 24
    # 新增金额 = 890,000 (89万)

    # 设定基准值 (随便设，只要比 0 大就行)
    BASE_QUANTITY = 1000
    BASE_AMOUNT   = 10000000 # 1000万

    # 设定今日值 = 基准值 + 你想要的增量
    TARGET_QUANTITY = BASE_QUANTITY + 24      # = 1024
    TARGET_AMOUNT   = BASE_AMOUNT   + 890000  # = 1089万


    # --- 3. 执行 SQL 插入 ---
    sql = """
    INSERT INTO raw_snapshots (scraped_at, total_amount, total_quantity)
    VALUES (%s, %s, %s);
    """

    try:
        with conn:
            with conn.cursor() as cur:
                # 1. 先清空旧数据 (防止数据干扰，保证纯净测试)
                cur.execute("TRUNCATE TABLE raw_snapshots CASCADE;")
                cur.execute("TRUNCATE TABLE daily_metrics CASCADE;")
                print("🧹 已清空旧数据...")

                # 2. 插入昨天的数据
                cur.execute(sql, (yesterday_snapshot, BASE_AMOUNT, BASE_QUANTITY))
                print(f"✅ 插入昨日基准 (UTC {yesterday_snapshot.strftime('%H:%M')}): 销量{BASE_QUANTITY}, 金额{BASE_AMOUNT}")

                # 3. 插入今天的数据
                cur.execute(sql, (today_snapshot, TARGET_AMOUNT, TARGET_QUANTITY))
                print(f"✅ 插入今日数据 (UTC {today_snapshot.strftime('%H:%M')}): 销量{TARGET_QUANTITY}, 金额{TARGET_AMOUNT}")

    except Exception as e:
        print(f"❌ 注入失败: {e}")
    finally:
        conn.close()
    
    print("\n🎉 数据注入完成！现在由于差值正好是 24 和 89万，")
    print("   运行 'python -m scraper.cli today-metrics' 应该能看到完美的结果。")

if __name__ == "__main__":
    seed()