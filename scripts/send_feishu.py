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


def extract_summary(content):
    """从 HTML 内容中提取摘要信息"""
    import re

    summary = []

    # 提取标题
    title_match = re.search(r'<h1[^>]*>([^<]+)</h1>', content, re.IGNORECASE)
    if title_match:
        summary.append(f"📌 {title_match.group(1).strip()}")

    # 提取统计信息 - 查找 stat-card 中的 number 和 label
    stats = re.findall(r'<div class="stat-card[^"]*">\s*<div class="number">(\d+)</div>\s*<div class="label">([^<]+)</div>', content)
    if stats:
        stats_text = []
        for num, label in stats:
            stats_text.append(f"{label}: {num}")
        summary.append(" | ".join(stats_text))
    else:
        # 备用：直接统计 topic-card 和 idea-card 数量
        topic_count = len(re.findall(r'<div class="topic-card"', content))
        idea_count = len(re.findall(r'<div class="idea-card"', content))
        if topic_count > 0:
            summary.append(f"话题数: {topic_count} | 创意数: {idea_count}")

    # 提取优秀和良好计数
    excellent_match = re.search(r'优秀创意.*?(\d+)', content)
    good_match = re.search(r'良好创意.*?(\d+)', content)
    if excellent_match:
        summary.append(f"✅ 优秀: {excellent_match.group(1)}个")
    if good_match:
        summary.append(f"👍 良好: {good_match.group(1)}个")

    # 提取前5个话题标题
    topic_titles = re.findall(r'<div class="topic-title">([^<]+)</div>', content)
    if topic_titles:
        summary.append("\n🔥 热门话题:")
        for i, title in enumerate(topic_titles[:5], 1):
            # 截断过长标题
            display_title = title[:25] + "..." if len(title) > 25 else title
            summary.append(f"{i}. {display_title}")

    return "\n\n".join(summary) if summary else "报告已生成"


def main():
    webhook_url = os.getenv("FEISHU_WEBHOOK_URL")
    report_path = os.getenv("REPORT_PATH", f"hot_search_report_{datetime.now().strftime('%y%m%d')}.html")
    report_url = os.getenv("REPORT_URL", "")
    status = os.getenv("STATUS", "success")

    print(f"DEBUG: REPORT_PATH={report_path}")
    print(f"DEBUG: REPORT_URL={report_url}")

    if not webhook_url:
        print("FEISHU_WEBHOOK_URL not set, skipping notification")
        sys.exit(0)

    # 读取报告内容
    try:
        with open(report_path, "r", encoding="utf-8") as f:
            content = f.read()
            print(f"DEBUG: Report loaded, size={len(content)} bytes")

        # 提取摘要
        summary = extract_summary(content)
        print(f"DEBUG: Summary extracted, length={len(summary)}")
        print(f"DEBUG: Summary preview: {summary[:200]}...")

    except FileNotFoundError:
        print(f"WARNING: Report file not found: {report_path}")
        summary = "❌ 报告文件未找到，请检查 GitHub Actions 日志"
    except Exception as e:
        print(f"ERROR: Failed to read report: {e}")
        summary = f"❌ 读取报告失败: {str(e)}"

    # 如果有URL，添加链接
    if report_url:
        summary += f"\n\n[👉 点击查看完整报告]({report_url})"

    send_feishu_webhook(webhook_url, summary, status)


if __name__ == "__main__":
    main()