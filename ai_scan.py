import requests
import json
import os
from dotenv import load_dotenv
import anthropic

# 加载 API Key
load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def get_markets(limit=20):
    """获取活跃市场"""
    url = f"https://gamma-api.polymarket.com/markets?active=true&closed=false&limit={limit}&order=volume&ascending=false&tag=finance"
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
                'total': round(yes_price + no_price, 4)
            })

        except:
            continue
    return result

def find_arb_with_ai(markets):
    """用 AI 找跨市场套利机会"""
    
    # 把市场列表整理成文字给 AI 看
    market_list = ""
    for i, m in enumerate(markets):
        market_list += f"{i+1}. {m['question']} (YES=${m['yes']}, NO=${m['no']})\n"
    
    prompt = f"""你是一个预测市场套利分析师，专门寻找定价错误。

以下是Polymarket上的活跃市场：
{market_list}

只关注以下两类机会：

1. 互补市场：两个市场的YES价格加起来不等于1（比如市场A YES=0.6，市场B YES=0.5，加起来1.1，说明定价有误）

2. 逻辑矛盾：如果A发生则B必然发生，但B的价格远低于A

只列出真实的套利机会，没有就直接说没有，不要分析不相关的市场。"""

    print("🤖 正在用 AI 分析市场关联...\n")
    
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    return message.content[0].text

# 主程序
print("📊 获取市场数据...\n")
markets = get_markets(20)
print(f"获取到 {len(markets)} 个市场\n")

for m in markets:
    print(f"  {m['question'][:50]}... YES=${m['yes']}")

print()
analysis = find_arb_with_ai(markets)
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("🤖 AI 分析结果：")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print(analysis)
