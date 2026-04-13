#!/usr/bin/env python3
"""
发送报告到飞书 Webhook
"""

import os
import sys
from datetime import datetime


def send_feishu_webhook(webhook_url, content, status="success"):
    """发送消息到飞书"""
    import urllib.request
    import json

    # 判断状态决定颜色
    color = "green" if status == "success" else "red"

    payload = {
        "msg_type": "interactive",
        "card": {
            "config": {"wide_screen_mode": True},
            "header": {
                "title": {"tag": "plain_text", "content": f"🔥 热搜产品创意分析报告 - {status.upper()}"},
                "template": color
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": content
                    }
                },
                {
                    "tag": "hr"
                },
                {
                    "tag": "note",
                    "elements": [
                        {"tag": "plain_text", "content": f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"}
                    ]
                }
            ]
        }
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        webhook_url,
        data=data,
        headers={"Content-Type": "application/json"}
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode("utf-8"))
            if result.get("code") == 0 or result.get("StatusCode") == 0:
                print("Message sent to Feishu successfully!")
                return True
            else:
                print(f"Feishu API error: {result}")
                return False
    except Exception as e:
        print(f"Failed to send Feishu message: {e}")
        return False


def main():
    webhook_url = os.getenv("FEISHU_WEBHOOK_URL")
    report_path = os.getenv("REPORT_PATH", f"hot_search_report_{datetime.now().strftime('%y%m%d')}.html")
    status = os.getenv("STATUS", "success")

    if not webhook_url:
        print("FEISHU_WEBHOOK_URL not set, skipping notification")
        sys.exit(0)

    # 读取报告内容
    try:
        with open(report_path, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        content = "报告文件未找到"

    # 提取摘要信息
    summary = []
    if "hot_topics" in content or "话题" in content:
        summary.append(f"📊 报告文件: `{report_path}`")
        summary.append(f"📅 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # 尝试提取统计信息
        if "优秀" in content:
            summary.append("✅ 已生成分析报告，请查看附件或访问 GitHub Actions 获取")
        elif "error" in content.lower() or "失败" in content:
            summary.append("❌ 报告生成遇到问题，请检查日志")
        else:
            summary.append("📋 报告已生成")

    else:
        summary.append("报告内容为空或格式异常")

    content_md = "\n\n".join(summary)

    send_feishu_webhook(webhook_url, content_md, status)


if __name__ == "__main__":
    main()
