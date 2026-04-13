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

## 筛选标准（必须严格按此筛选）

只选择与以下高度相关的话题：
- 心理健康：焦虑、抑郁、失眠、心理问题、情绪崩溃、心理咨询等
- 情绪管理：情绪失控、发脾气、心态调整、正念、冥想等
- 职场心理：职场PUA、加班焦虑、裁员恐慌、35岁危机、职场抑郁等
- 情感关系：恋爱、婚姻、相亲、离婚、单身焦虑、家庭矛盾等
- 年轻人状态：躺平、摆烂、佛系、内卷、焦虑、迷茫、空巢青年等

## 输出要求

筛选5-8条最相关的话题，输出简洁的 Markdown 表格：

| # | 话题 | 产品创意 | 评分 |
|---|------|----------|------|
| 1 | 话题名 | 创意名（功能简述） | XX分 |

每个话题下附1-2个产品创意：
- 名称：xxx
- 核心功能：xxx
- 目标用户：xxx

## 注意
- 话题必须与心理健康/情绪管理强相关
- 创意要轻量（小程序/轻应用）
- 只输出最终结果，不要描述过程
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
    <title>热搜产品创意分析报告</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 40px 20px;
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.15);
            overflow: hidden;
        }}
        header {{
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        header h1 {{
            font-size: 2em;
            margin-bottom: 10px;
        }}
        header .meta {{
            opacity: 0.9;
            font-size: 0.95em;
        }}
        .content {{
            padding: 40px;
        }}
        h2 {{
            color: #667eea;
            font-size: 1.4em;
            margin: 30px 0 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #f0f0f0;
        }}
        h2:first-child {{
            margin-top: 0;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            font-size: 0.95em;
        }}
        th, td {{
            padding: 16px 12px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }}
        th {{
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            font-weight: 600;
        }}
        tr:hover {{
            background-color: #f8f6ff;
        }}
        .score {{
            font-weight: bold;
            color: #667eea;
        }}
        .idea {{
            background: #f8f6ff;
            border-radius: 12px;
            padding: 20px;
            margin: 15px 0;
            border-left: 4px solid #667eea;
        }}
        .idea h4 {{
            color: #333;
            margin-bottom: 10px;
        }}
        .idea p {{
            color: #666;
            line-height: 1.6;
        }}
        code {{
            background: #f4f4f4;
            padding: 2px 8px;
            border-radius: 4px;
            font-family: Monaco, monospace;
        }}
        pre {{
            background: #f4f4f4;
            padding: 15px;
            border-radius: 8px;
            overflow-x: auto;
        }}
        ul {{
            padding-left: 20px;
        }}
        li {{
            margin: 8px 0;
            color: #555;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🔥 热搜产品创意分析报告</h1>
            <p class="meta">生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
        </header>
        <div class="content">
            {html_body}
        </div>
    </div>
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
