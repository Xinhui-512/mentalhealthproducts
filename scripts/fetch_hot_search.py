#!/usr/bin/env python3
"""
获取微博和抖音热搜数据
API: 天聚数行 (https://apis.tianapi.com)
"""

import json
import os
import requests
from datetime import datetime

# 天聚数行 API Keys
WEIBO_API_KEY = os.getenv("WEIBO_API_KEY")
DOUYIN_API_KEY = os.getenv("DOUYIN_API_KEY")


def fetch_weibo_hot():
    """获取微博热搜"""
    url = "https://apis.tianapi.com/weibohot/index"
    params = {"key": WEIBO_API_KEY}
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        if data.get("code") == 200:
            return data.get("result", [])
        else:
            print(f"Weibo API error: {data.get('msg')}")
            return []
    except Exception as e:
        print(f"Weibo API exception: {e}")
        return []


def fetch_douyin_hot():
    """获取抖音热搜"""
    url = "https://apis.tianapi.com/douyinhot/index"
    params = {"key": DOUYIN_API_KEY}
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        if data.get("code") == 200:
            return data.get("result", [])
        else:
            print(f"Douyin API error: {data.get('msg')}")
            return []
    except Exception as e:
        print(f"Douyin API exception: {e}")
        return []


def main():
    today = datetime.now().strftime("%Y-%m-%d")

    # Debug: 检查 API key 是否配置
    if not WEIBO_API_KEY:
        print("ERROR: WEIBO_API_KEY is not set")
    if not DOUYIN_API_KEY:
        print("ERROR: DOUYIN_API_KEY is not set")

    weibo_data = fetch_weibo_hot()
    douyin_data = fetch_douyin_hot()

    # 转换为统一格式
    hot_list = []

    for item in weibo_data:
        hot_list.append({
            "platform": "微博",
            "rank": item.get("rank", 0),
            "topic": item.get("word", ""),
            "hot_value": item.get("hotnum", 0),
            "date": today,
            "source": "微博热搜"
        })

    for item in douyin_data:
        hot_list.append({
            "platform": "抖音",
            "rank": item.get("rank", 0),
            "topic": item.get("word", ""),
            "hot_value": item.get("hotnum", 0),
            "date": today,
            "source": "抖音热搜"
        })

    # 保存热搜数据
    with open("weibo_hot.json", "w", encoding="utf-8") as f:
        json.dump({
            "fetch_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "hot_list": hot_list
        }, f, ensure_ascii=False, indent=2)

    print(f"Fetched {len(weibo_data)} weibo + {len(douyin_data)} douyin topics")


if __name__ == "__main__":
    main()
