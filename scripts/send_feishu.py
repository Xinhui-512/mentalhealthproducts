#!/usr/bin/env python3
"""
发送报告到飞书 Webhook
"""

import os
import sys
from datetime import datetime


def create_gist(token, filename, content, description="热搜产品创意分析报告"):
    """上传报告到 GitHub Gist 并返回链接"""
    import urllib.request
    import json

    payload = {
        "description": description,
        "public": False,
        "files": {
            filename: {"content": content}
        }
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        "https://api.github.com/gists",
        data=data,
        headers={
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            result = json.loads(response.read().decode("utf-8"))
            gist_url = result.get("html_url", "")
            raw_url = result.get("files", {}).get(filename, {}).get("raw_url", "")
            print(f"DEBUG: Gist created - {gist_url}")
            return gist_url, raw_url
    except Exception as e:
        print(f"WARNING: Failed to create Gist: {e}")
        return "", ""


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
    gh_token = os.getenv("GH_TOKEN")
    status = os.getenv("STATUS", "success")

    print(f"DEBUG: REPORT_PATH={report_path}")

    if not webhook_url:
        print("FEISHU_WEBHOOK_URL not set, skipping notification")
        sys.exit(0)

    # 读取报告内容
    gist_url = ""
    try:
        with open(report_path, "r", encoding="utf-8") as f:
            content = f.read()
            print(f"DEBUG: Report loaded, size={len(content)} bytes")

        # 上传到 GitHub Gist
        if gh_token and content:
            gist_url, raw_url = create_gist(gh_token, os.path.basename(report_path), content)
            if gist_url:
                print(f"DEBUG: Report uploaded to Gist: {gist_url}")

    except FileNotFoundError:
        print(f"WARNING: Report file not found: {report_path}")
        content = ""

    # 构建飞书消息
    summary = []
    summary.append(f"📊 报告文件: `{os.path.basename(report_path)}`")
    summary.append(f"📅 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if gist_url:
        summary.append(f"✅ 报告已生成")
        summary.append(f"\n[点击查看完整报告]({gist_url})")
    elif content:
        summary.append("📋 报告已生成（上传失败，请查看 GitHub Actions）")
    else:
        summary.append("❌ 报告生成失败，请检查日志")

    content_md = "\n\n".join(summary)

    send_feishu_webhook(webhook_url, content_md, status)


if __name__ == "__main__":
    main()