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
    
    prompt = f"""你是一个预测市场套利分析师。

以下是 Polymarket 上的活跃市场列表：

{market_list}

请找出哪些市场之间存在逻辑关联，并判断它们的价格是否矛盾。

例如：
- 如果市场A的结果会直接影响市场B的结果
- 但两个市场的价格不一致
- 这就是套利机会

请列出你发现的逻辑关联和价格矛盾，格式如下：
市场X 和 市场Y 相关，原因：[解释]，价格矛盾：[是/否]，套利建议：[具体操作]"""

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
