#!/usr/bin/env python3
"""
调用 MiniMax Claude API 生成热搜产品创意分析报告
API: https://api.minimaxi.com/anthropic
模型: MiniMax-M2.7
"""

import anthropic
import json
import os
import sys
from datetime import datetime

# MiniMax API 配置
MINIMAX_API_KEY = os.getenv("MINIMAX_API_KEY")
MINIMAX_API_URL = os.getenv("MINIMAX_API_URL", "https://api.minimaxi.com/anthropic")

# 读取 SKILL.md 作为分析标准
with open("skills/hot-search-ideas/SKILL.md", "r", encoding="utf-8") as f:
    skill_content = f.read()

# 读取热搜数据
with open("weibo_hot.json", "r", encoding="utf-8") as f:
    hot_data = json.load(f)


def build_prompt():
    """构建分析提示词"""
    today = datetime.now().strftime("%Y-%m-%d")
    date_str = datetime.now().strftime("%y%m%d")

    return f"""# 热搜产品创意分析任务

## 当前日期
{today}

## 热搜数据
{json.dumps(hot_data, ensure_ascii=False, indent=2)}

## 输出要求

从热搜中筛选10-15条最相关的话题，输出格式：

### 统计概览
- 分析话题数：X
- 优秀创意：X个 | 良好创意：X个

### 产品创意列表

| 排名 | 话题 | 产品创意 | 评分 | 等级 |
|------|------|----------|------|------|
| 1 | 话题名 | 创意名称+核心功能 | XX分 | 优秀/良好/一般 |

每个创意格式：
**话题：** xxx
**产品创意：** xxx（功能：xxx）
**评分：** 有趣度XX + 有用度XX = 总分XX
**等级：** 优秀/良好/一般

## 注意
- 只输出最终结果，不要描述过程
- 产品创意要简单轻量
- 输出纯Markdown
"""


def main():
    if not MINIMAX_API_KEY:
        raise ValueError("MINIMAX_API_KEY environment variable is not set. Please configure it in GitHub Secrets.")

    client = anthropic.Anthropic(
        api_key=MINIMAX_API_KEY,
        base_url=MINIMAX_API_URL
    )

    prompt = build_prompt()
    date_str = datetime.now().strftime("%y%m%d")
    output_file = f"hot_search_report_{date_str}.html"

    print(f"Starting AI analysis... Output: {output_file}")

    try:
        message = client.messages.create(
            model="MiniMax-M2.7",
            max_tokens=16384,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        # 解析响应并保存HTML报告
        # 处理可能的 ThinkingBlock
        response_text = None
        for block in message.content:
            if hasattr(block, 'text') and block.text:
                response_text = block.text
                break

        if response_text is None:
            raise ValueError("No text content found in response")

        print(f"DEBUG: Response length = {len(response_text)} chars")
        print(f"DEBUG: Response ends with: ...{response_text[-200:]}")
        print(f"DEBUG: Stop reason: {message.stop_reason if hasattr(message, 'stop_reason') else 'N/A'}")

        # 如果响应是完整的HTML，直接保存
        if "<html" in response_text.lower() or "<!doctype" in response_text.lower():
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(response_text)
            print(f"Report saved to {output_file}")
        else:
            # 将 Markdown 转换为 HTML
            import markdown
            html_body = markdown.markdown(
                response_text,
                extensions=['tables', 'fenced_code']
            )

            html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>热搜产品创意分析 {date_str}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; line-height: 1.6; }}
        h1 {{ color: #333; border-bottom: 2px solid #667eea; padding-bottom: 10px; }}
        h2 {{ color: #555; margin-top: 30px; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background-color: #667eea; color: white; }}
        tr:nth-child(even) {{ background-color: #f9f9f9; }}
        code {{ background-color: #f4f4f4; padding: 2px 6px; border-radius: 3px; }}
        pre {{ background-color: #f4f4f4; padding: 15px; border-radius: 5px; overflow-x: auto; }}
    </style>
</head>
<body>
    <h1>热搜产品创意分析报告</h1>
    <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    <hr>
    {html_body}
</body>
</html>"""
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(html_content)
            print(f"Report saved to {output_file}")

        print("Analysis completed successfully!")

    except Exception as e:
        print(f"Error: {e}")
        # 创建错误报告
        error_html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>错误报告</title>
</head>
<body>
    <h1>生成失败</h1>
    <p>错误信息: {str(e)}</p>
    <p>时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
</body>
</html>"""
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(error_html)
        raise


if __name__ == "__main__":
    main()
