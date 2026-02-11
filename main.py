import os
import json
import requests
from fastapi import FastAPI, Request
from scraper.cli import get_report_text

app = FastAPI()

# 🔴 从环境变量获取飞书配置 (稍后在 Railway 设置)
APP_ID = os.environ.get("FEISHU_APP_ID")
APP_SECRET = os.environ.get("FEISHU_APP_SECRET")

def get_tenant_access_token():
    """获取飞书 API 调用凭证"""
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    resp = requests.post(url, json={"app_id": APP_ID, "app_secret": APP_SECRET})
    return resp.json().get("tenant_access_token")

def reply_message(message_id, text):
    """回复消息给飞书"""
    token = get_tenant_access_token()
    url = f"https://open.feishu.cn/open-apis/im/v1/messages/{message_id}/reply"
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "content": json.dumps({"text": text}),
        "msg_type": "text"
    }
    requests.post(url, headers=headers, json=payload)

@app.post("/feishu/webhook")
async def feishu_webhook(request: Request):
    """接收飞书事件的回调接口"""
    payload = await request.json()
    
    # 1. 处理飞书的 "Challenge" (第一次配置必须)
    if "challenge" in payload:
        return {"challenge": payload["challenge"]}
    
    # 2. 处理正常消息事件
    # 飞书的结构比较深: event -> message -> content
    event = payload.get("event", {})
    if event.get("message", {}).get("message_type") == "text":
        message_id = event["message"]["message_id"]
        # 解析消息内容 (它是 JSON 字符串格式)
        content = json.loads(event["message"]["content"])
        text = content.get("text", "")
        
        # 3. 判断指令 (只要包含 "销量" 或 "战报" 就触发)
        if "销量" in text or "战报" in text:
            # 运行你的爬虫逻辑
            report = get_report_text()
            # 回复消息
            reply_message(message_id, report)
            
    return {"status": "ok"}