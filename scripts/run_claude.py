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

筛选5-8条最相关的话题，对每条话题按以下格式输出：

### 话题 N：[话题名称]
**热度排名**：第X名 | **平台**：微博/抖音

**事件概要**：
（请根据你的知识，简要描述这个热搜话题的背景、最新动态或引发讨论的原因，50-150字）

**产品创意**：
- **创意名称**：xxx
- **核心功能**：xxx
- **目标用户**：xxx
- **有趣度评分**：XX/100
- **有用度评分**：XX/100
- **综合评分**：XX分

---

请为每个话题都生成详细的事件概要，让读者能快速了解发生了什么。不要只输出表格，要输出完整的内容区块。

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
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Microsoft YaHei", sans-serif;
    background: #0f0f1a;
    color: #e8e8f0;
    line-height: 1.6;
    padding: 24px 16px;
  }}
  .container {{ max-width: 860px; margin: 0 auto; }}

  .header {{
    text-align: center;
    padding: 40px 20px;
    background: linear-gradient(135deg, #1a1a2e, #16213e);
    border-radius: 16px;
    margin-bottom: 28px;
    border: 1px solid rgba(255,255,255,0.06);
  }}
  .header h1 {{
    font-size: 26px;
    font-weight: 700;
    background: linear-gradient(90deg, #f5a623, #ff6b6b);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 8px;
  }}
  .header .meta {{ font-size: 13px; color: #888; margin-top: 6px; }}

  .stats-bar {{ display: flex; gap: 16px; flex-wrap: wrap; margin-bottom: 28px; }}
  .stat-card {{
    flex: 1; min-width: 120px; background: #1a1a2e;
    border-radius: 10px; padding: 16px; text-align: center;
    border: 1px solid rgba(255,255,255,0.05);
  }}
  .stat-card .num {{ font-size: 28px; font-weight: 700; color: #f5a623; }}
  .stat-card .label {{ font-size: 12px; color: #888; margin-top: 4px; }}

  .legend {{ display: flex; gap: 20px; flex-wrap: wrap; margin-bottom: 24px; font-size: 13px; color: #aaa; }}
  .legend span {{ display: flex; align-items: center; gap: 6px; }}
  .dot {{ width: 10px; height: 10px; border-radius: 50%; display: inline-block; }}
  .dot.gold {{ background: #f5a623; }}
  .dot.silver {{ background: #94a3b8; }}
  .dot.normal {{ background: #555; }}

  .hot-item {{
    background: #1a1a2e; border-radius: 12px; margin-bottom: 20px;
    overflow: hidden; border: 1px solid rgba(255,255,255,0.05);
  }}
  .hot-item.gold {{ border-color: rgba(245,166,35,0.3); box-shadow: 0 0 20px rgba(245,166,35,0.06); }}
  .hot-item.silver {{ border-color: rgba(148,163,184,0.2); }}

  .item-header {{ display: flex; align-items: center; padding: 16px 20px; gap: 14px; cursor: pointer; }}
  .rank-badge {{
    width: 36px; height: 36px; border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    font-weight: 700; font-size: 15px; flex-shrink: 0;
    background: #252540; color: #ccc;
  }}
  .rank-badge.top3 {{ background: linear-gradient(135deg, #f5a623, #ff6b6b); color: #fff; }}
  .topic-info {{ flex: 1; }}
  .topic-name {{ font-size: 16px; font-weight: 600; color: #f0f0f5; margin-bottom: 4px; }}
  .topic-meta {{ font-size: 12px; color: #777; }}
  .topic-meta .source {{ color: #f5a623; }}
  .expand-icon {{ font-size: 18px; color: #555; transition: transform 0.2s; }}
  .expand-icon.open {{ transform: rotate(180deg); }}
  .item-body {{ display: none; padding: 0 20px 20px; }}
  .item-body.show {{ display: block; }}

  .event-summary {{
    background: #1a2535; border-radius: 8px; padding: 14px 16px;
    font-size: 14px; color: #b8c5d6; line-height: 1.7; margin-bottom: 16px;
    border-left: 3px solid #4a9eff;
  }}

  .ideas-section {{
    background: #1a1a30; border-radius: 10px; padding: 16px;
    margin-top: 12px;
  }}
  .ideas-section h3 {{
    font-size: 13px; color: #f5a623; text-transform: uppercase;
    letter-spacing: 1px; margin-bottom: 12px;
  }}
  .idea-card {{
    background: #252545; border-radius: 10px; padding: 14px 16px;
    margin-bottom: 10px; border: 1px solid rgba(255,255,255,0.06);
  }}
  .idea-name {{ font-size: 15px; font-weight: 600; color: #e0e0f0; margin-bottom: 6px; }}
  .idea-funcs {{ font-size: 13px; color: #aaa; margin-bottom: 10px; }}
  .idea-funcs strong {{ color: #f5a623; margin-right: 4px; }}
  .idea-target {{ font-size: 12px; color: #777; margin-bottom: 10px; }}
  .score-row {{ display: flex; align-items: center; gap: 10px; font-size: 12px; }}
  .score-label {{ color: #888; min-width: 50px; }}
  .score-bar-wrap {{ flex: 1; background: #2a2a45; border-radius: 4px; height: 6px; }}
  .score-bar {{ height: 100%; border-radius: 4px; transition: width 0.5s; }}
  .score-bar.fun {{ background: linear-gradient(90deg, #ff6b6b, #f5a623); }}
  .score-bar.util {{ background: linear-gradient(90deg, #4ade80, #34d399); }}
  .score-num {{ min-width: 36px; text-align: right; color: #ccc; }}

  .total-score {{
    display: inline-flex; align-items: center; gap: 6px;
    margin-top: 10px; padding: 4px 10px; border-radius: 20px;
    font-size: 12px; font-weight: 600;
  }}
  .total-score.excellent {{ background: rgba(245,166,35,0.15); color: #f5a623; border: 1px solid rgba(245,166,35,0.3); }}
  .total-score.good {{ background: rgba(148,163,184,0.1); color: #94a3b8; border: 1px solid rgba(148,163,184,0.2); }}
  .total-score.normal {{ background: rgba(100,100,130,0.1); color: #777; border: 1px solid rgba(100,100,130,0.2); }}

  .footer {{ text-align: center; padding: 24px; font-size: 12px; color: #555; }}

  h2 {{ color: #667eea; font-size: 1.4em; margin: 30px 0 20px; padding-bottom: 10px; border-bottom: 2px solid #f0f0f0; }}
  table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
  th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #333; }}
  th {{ background: linear-gradient(135deg, #667eea, #764ba2); color: white; }}
  tr:hover {{ background-color: #1a1a2e; }}
  code {{ background: #1e1e38; padding: 2px 8px; border-radius: 4px; font-family: Monaco, monospace; }}
  pre {{ background: #1e1e38; padding: 15px; border-radius: 8px; overflow-x: auto; }}
  ul, li {{ color: #c0c0d0; }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>🔥 热搜产品创意分析报告</h1>
    <div class="meta">微博热搜 · {datetime.now().strftime('%Y年%m月%d日')} · 心理健康 × 个人成长</div>
  </div>
  <div class="content">
    {html_body}
  </div>
  <div class="footer">
    报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')} · 数据来源：微博热搜API · 筛选标准：心理健康/个人成长/情绪管理相关
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
