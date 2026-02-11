import psycopg2
import sys

# 🔴 请将下面的链接替换为你从 Railway 复制的 "Postgres Connection URL"
# 格式应该是: "postgresql://postgres:password@roundhouse.proxy.rlwy.net:..."
DB_URL = "postgresql://postgres:TrTTXxyJgMrapHqhFRdiYKezsMcTIEYn@ballast.proxy.rlwy.net:56706/railway"

def upgrade_schema():
    print("正在连接 Railway 远程数据库...")
    
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        
        print("连接成功！开始执行数据库升级指令...")

        # 执行 SQL 语句：增加 8 个新字段
        sql_commands = [
            "ALTER TABLE daily_metrics ADD COLUMN IF NOT EXISTS goal_daily_amount BIGINT DEFAULT 0;",
            "ALTER TABLE daily_metrics ADD COLUMN IF NOT EXISTS goal_daily_quantity INTEGER DEFAULT 0;",
            "ALTER TABLE daily_metrics ADD COLUMN IF NOT EXISTS goal_total_amount BIGINT DEFAULT 0;",
            "ALTER TABLE daily_metrics ADD COLUMN IF NOT EXISTS goal_total_quantity INTEGER DEFAULT 0;",
            
            "ALTER TABLE daily_metrics ADD COLUMN IF NOT EXISTS diff_daily_amount BIGINT DEFAULT 0;",
            "ALTER TABLE daily_metrics ADD COLUMN IF NOT EXISTS diff_daily_quantity INTEGER DEFAULT 0;",
            "ALTER TABLE daily_metrics ADD COLUMN IF NOT EXISTS diff_total_amount BIGINT DEFAULT 0;",
            "ALTER TABLE daily_metrics ADD COLUMN IF NOT EXISTS diff_total_quantity INTEGER DEFAULT 0;"
        ]

        for command in sql_commands:
            cur.execute(command)
            # 简单的打印，确认执行进度
            print(f"Executed: {command[:50]}...")

        conn.commit()
        cur.close()
        conn.close()
        print("\n✅ 数据库升级成功！新字段已添加。")

    except Exception as e:
        print(f"\n❌ 升级失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    upgrade_schema()