import requests
import json
import os
from dotenv import load_dotenv
import anthropic

load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def get_markets(limit=50):
    url = f"https://gamma-api.polymarket.com/markets?active=true&closed=false&limit={limit}&order=volume&ascending=false"
    response = requests.get(url)
    markets = response.json()
    
    result = []
    for market in markets:
        outcome_prices_raw = market.get('outcomePrices')
        if not outcome_prices_raw:
            continue
        try:
            prices = json.loads(outcome_prices_raw)
            if len(prices) != 2:
                continue
            yes_price = float(prices[0])
            no_price = float(prices[1])
            if yes_price == 0 and no_price == 0:
                continue
            result.append({
                'question': market.get('question'),
                'yes': yes_price,
                'no': no_price,
                'volume': float(market.get('volume') or 0)
            })
        except:
            continue
    return result

def smart_arb_analysis(markets):
    """严格的套利分析"""
    market_list = ""
    for i, m in enumerate(markets[:30]):
        market_list += f"{i+1}. {m['question']} (YES=${m['yes']}, 交易量=${m['volume']:,.0f})\n"
    
    prompt = f"""你是一个严格的预测市场套利分析师。

以下是 Polymarket 市场列表：
{market_list}

请找出真正的套利机会。真正的套利机会必须同时满足：

1. 逻辑关联：市场A的结果会直接影响市场B（比如：赢得选举 → 必然控制国会）
2. 价格矛盾：两个市场的价格在逻辑上不一致（比如：A=65% 但 B=40%，而B应该>=A）
3. 可操作性：交易量 > $1000（流动性够用）

对于每个机会，请按这个格式输出：

---
机会：市场A名称 vs 市场B名称
逻辑关系：为什么A影响B
价格矛盾：A的YES=多少 但逻辑上应该高于或低于 B的YES=多少
操作建议：买入哪个市场的YES或NO
风险提示：有什么可能让这个套利失败
置信度：高或中或低
---

如果没有找到真正符合条件的机会，请直接说"本次扫描未发现高质量套利机会"，不要勉强凑机会。"""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text

# 主程序
print("📊 获取市场数据...\n")
markets = get_markets(50)
print(f"获取到 {len(markets)} 个市场\n")

print("🤖 严格分析中...\n")
result = smart_arb_analysis(markets)

print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("🎯 分析结果：")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print(result)