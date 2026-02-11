import psycopg2
import sys
import os

# 🔴 请务必将下面的链接替换为你从 Railway 复制的 "Postgres Connection URL"
# 如果你已经配置了本地 .env 文件，也可以尝试直接用 os.environ.get("DATABASE_URL")
# 为了保险，建议你直接把链接粘贴在下面引号里：
DB_URL = "postgresql://postgres:TrTTXxyJgMrapHqhFRdiYKezsMcTIEYn@ballast.proxy.rlwy.net:56706/railway"

def fix_column():
    print("正在连接 Railway 远程数据库...")
    
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        
        print("连接成功！正在补全缺失的 'updated_at' 字段...")

        # 执行 SQL 语句：增加 updated_at 字段
        sql = "ALTER TABLE daily_metrics ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();"
        
        cur.execute(sql)
        conn.commit()
        
        cur.close()
        conn.close()
        print("\n✅ 修复成功！字段 'updated_at' 已添加。")

    except Exception as e:
        print(f"\n❌ 修复失败: {e}")

if __name__ == "__main__":
    fix_column()