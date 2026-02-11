## Makuake iFLYTEK AIWATCH 爬虫

这个项目是一个 Python 爬虫，用来每小时抓取 Makuake 项目 `iFLYTEK AIWATCH` 的页面数据：

- 目标 URL：`https://www.makuake.com/project/iflytek_aiwtch/`
- 抓取字段：
  - 日元销售额（通过给定 XPath）
  - 销量（通过给定 XPath）
- 将抓取结果按时间存入云端数据库（推荐 Railway 的 PostgreSQL）
- 按每天的基准点（前一天 23:00 的累计值）计算「今日销量」与「今日销售额」

### 本地快速开始

1. 创建并激活虚拟环境（可选）
2. 安装依赖：

```bash
pip install -r requirements.txt
```

3. 设置环境变量（本地可用 `.env` 文件）：

```env
DATABASE_URL=postgresql://user:password@host:port/dbname
TZ=Asia/Shanghai
```

4. 初始化数据库表：

```bash
python -m scraper.init_db
```

5. 运行一次抓取（调试用）：

```bash
python -m scraper.cli scrape-once
```

6. 计算当前「今日销量/销售额」：

```bash
python -m scraper.cli today-metrics
```

### 在 Railway 上部署（概要）

- 将本仓库推到 GitHub
- 在 Railway 创建项目并连接仓库
- 添加 PostgreSQL 插件，将连接串配置为环境变量 `DATABASE_URL`
- 设置定时任务：
  - 每小时运行：`python -m scraper.jobs run_hourly`
  - 每天 23:00（或 23:05）运行：`python -m scraper.jobs compute_daily`

详细部署步骤可以根据 Railway 的最新文档调整。

