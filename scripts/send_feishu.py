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

    # 提取统计信息
    stats = []

    # 热搜话题数量
    topic_count = len(re.findall(r'<tr[^>]*class=["\']topic', content, re.IGNORECASE))
    if topic_count == 0:
        # 尝试其他方式统计
        topic_count = content.count('topic') // 3  # 粗略估计

    if topic_count > 0:
        stats.append(f"话题数: {topic_count}")

    # 提取评分信息
    excellent = content.count('优秀') + content.count('gold') + content.count('#ffd700')
    good = content.count('良好') + content.count('silver') + content.count('#c0c0c0')

    if excellent > 0:
        stats.append(f"优秀: {excellent}个")
    if good > 0:
        stats.append(f"良好: {good}个")

    if stats:
        summary.append(" | ".join(stats))

    # 提取前几个话题标题
    topics = re.findall(r'<td[^>]*>(\d+)</td>\s*<td[^>]*>([^<]+)</td>', content)
    if topics:
        top_topics = []
        for i, (rank, title) in enumerate(topics[:5]):
            top_topics.append(f"#{rank} {title[:20]}...")
        if top_topics:
            summary.append("\n🔥 热门话题:")
            summary.append("\n".join(top_topics))

    return "\n\n".join(summary) if summary else "报告已生成"


def main():
    webhook_url = os.getenv("FEISHU_WEBHOOK_URL")
    report_path = os.getenv("REPORT_PATH", f"hot_search_report_{datetime.now().strftime('%y%m%d')}.html")
    status = os.getenv("STATUS", "success")

    print(f"DEBUG: REPORT_PATH={report_path}")

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

    except FileNotFoundError:
        print(f"WARNING: Report file not found: {report_path}")
        summary = "❌ 报告文件未找到，请检查 GitHub Actions 日志"
    except Exception as e:
        print(f"ERROR: Failed to read report: {e}")
        summary = f"❌ 读取报告失败: {str(e)}"

    send_feishu_webhook(webhook_url, summary, status)


if __name__ == "__main__":
    main()