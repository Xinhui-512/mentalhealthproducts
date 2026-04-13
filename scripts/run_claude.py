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

## 分析标准 (SKILL.md)
{skill_content}

## 任务要求

1. **读取热搜数据**：从 weibo_hot.json 读取微博和抖音热搜数据
2. **内容筛选**：筛选与以下主题相关的话题（不少于10条）：
   - 职场压力、生存状态、情感婚恋、家庭关系
   - 心理健康、社会现象、消费心理
3. **搜索详情**：使用 WebSearch 工具搜索每个话题的热点详情
4. **生成创意**：为每个话题生成产品创意，评分标准：
   - 有趣度 (80分)：趣味性、话题性、传播潜力
   - 有用度 (20分)：解决用户需求的程度
   - 总分 = 有趣度 × 0.8 + 有用度 × 0.2
5. **生成报告**：输出 HTML 报告，保存为 hot_search_report_{date_str}.html

## 输出格式

报告必须包含：
- 标题区：报告标题、生成时间
- 统计概览：热搜数量、分析话题数、优秀/良好评级分布
- 热点列表（按总分降序排列）：
  - 热点话题和排名
  - 日期、来源
  - 事件脉络详情
  - 产品创意列表（含评分）
  - 综合评分及等级标识

评分等级：
- 优秀 (≥80分)：金色高亮
- 良好 (60-80分)：银色/蓝色
- 一般 (<60分)：普通显示

## 注意事项
- 产品创意要简单轻量，优先小程序/轻应用
- 要接地气，避免过于天马行空
- 中文内容使用UTF-8编码
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
