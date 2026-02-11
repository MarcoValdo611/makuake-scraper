import psycopg2
import sys

# ==========================================
# 🔴以此处为准：请把你的 Railway 数据库链接粘贴在引号里
# 去 Railway -> Postgres -> Connect -> Copy "Postgres Connection URL"
# 格式通常是 postgresql://postgres:password@roundhouse.proxy.rlwy.net:PORT/railway
# ==========================================
DB_URL = "postgresql://postgres:TrTTXxyJgMrapHqhFRdiYKezsMcTIEYn@ballast.proxy.rlwy.net:56706/railway"


def diagnose():
    print(f"正在连接远程数据库: {DB_URL[:20]}...")
    
    try:
        # 1. 连接数据库
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        
        # 2. 查询 daily_metrics 表的结构
        table_name = 'daily_metrics'
        cur.execute(f"""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = '{table_name}'
            ORDER BY ordinal_position;
        """)
        columns = cur.fetchall()

        # 3. 输出诊断结果
        print(f"\n====== 表结构诊断: {table_name} ======")
        
        if not columns:
            print(f"❌ 严重错误: 表 '{table_name}' 不存在！")
            print("建议: 请检查是否运行过 init-db，或者表名是否正确。")
        else:
            print(f"✅ 表存在，共找到 {len(columns)} 个字段：\n")
            
            # 打印表头
            print(f"{'字段名 (Column)':<25} | {'类型 (Type)':<20}")
            print("-" * 50)
            
            # 关键字段检查清单
            required_columns = [
                'updated_at', 
                'goal_daily_amount', 'goal_daily_quantity',
                'diff_daily_amount', 'diff_daily_quantity'
            ]
            existing_cols = []

            for col_name, data_type in columns:
                print(f"{col_name:<25} | {data_type}")
                existing_cols.append(col_name)
            
            print("-" * 50)

            # 4. 自动检查缺失
            missing = [col for col in required_columns if col not in existing_cols]
            
            if missing:
                print(f"\n❌ 警告: 发现缺失关键字段！程序可能会崩溃。")
                print(f"缺失列表: {missing}")
            else:
                print("\n✅ 完美: 所有关键字段 (updated_at, goal_*, diff_*) 都存在。")

        cur.close()
        conn.close()

    except Exception as e:
        print(f"\n❌ 连接失败: {e}")
        print("提示: 请检查 DB_URL 是否正确，且没有任何多余的空格或引号。")

if __name__ == "__main__":
    # 简单的防呆检查
    if "你的_RAILWAY" in DB_URL:
        print("⚠️  请先修改脚本第 9 行，填入真实的 Railway 数据库链接！")
    else:
        diagnose()