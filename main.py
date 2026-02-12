import os
import json
import requests
from fastapi import FastAPI, Request
from scraper.cli import get_report_text

app = FastAPI()

# 🔴 从环境变量获取飞书配置
APP_ID = os.environ.get("FEISHU_APP_ID")
APP_SECRET = os.environ.get("FEISHU_APP_SECRET")

# ✅ 关键新增：根路径心跳接口 (解决 Railway 502 报错的核心)
# Railway 会定期访问这个接口来确认服务是否存活
@app.get("/")
async def root():
    return {
        "status": "alive",
        "message": "Makuake Bot is running correctly!"
    }

def get_tenant_access_token():
    """获取飞书 API 调用凭证"""
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    # 如果没有配置环境变量，这里可能会报错，建议加个判断或者 try-except，但目前保持简单
    resp = requests.post(url, json={"app_id": APP_ID, "app_secret": APP_SECRET})
    return resp.json().get("tenant_access_token")

def reply_message(message_id, text):
    """回复消息给飞书"""
    token = get_tenant_access_token()
    if not token:
        print("❌ 无法获取飞书 Token，请检查环境变量 FEISHU_APP_ID 和 SECRET")
        return

    url = f"https://open.feishu.cn/open-apis/im/v1/messages/{message_id}/reply"
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "content": json.dumps({"text": text}),
        "msg_type": "text"
    }
    resp = requests.post(url, headers=headers, json=payload)
    # 打印一下回复结果，方便在 Railway 日志里排查
    print(f"Reply sent: {resp.status_code}, {resp.text}")

@app.post("/feishu/webhook")
async def feishu_webhook(request: Request):
    """接收飞书事件的回调接口"""
    try:
        payload = await request.json()
    except Exception:
        return {"error": "Invalid JSON"}
    
    # 1. 处理飞书的 "Challenge" (第一次配置网址时必须)
    if "challenge" in payload:
        return {"challenge": payload["challenge"]}
    
    # 2. 处理正常消息事件
    # 飞书的结构: event -> message -> content
    event = payload.get("event", {})
    
    # 增加一点日志，方便在 Railway 看到收到了什么
    print(f"Received event: {json.dumps(event)}")

    if event.get("message", {}).get("message_type") == "text":
        message_id = event["message"]["message_id"]
        
        # 解析消息内容
        # 注意：content 是一个 JSON 字符串，需要二次解析
        try:
            content_str = event["message"]["content"]
            content = json.loads(content_str)
            text = content.get("text", "")
        except Exception as e:
            print(f"Error parsing content: {e}")
            return {"status": "error parsing content"}
        
        # 3. 判断指令
        if "销量" in text or "战报" in text:
            print("触发关键词，正在生成战报...")
            # 运行爬虫逻辑
            report = get_report_text()
            # 回复消息
            reply_message(message_id, report)
            
    return {"status": "ok"}
