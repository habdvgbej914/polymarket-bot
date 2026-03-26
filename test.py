import requests
import json

url = "https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=100&order=volume&ascending=false"

response = requests.get(url)
markets = response.json()

print(f"扫描 {len(markets)} 个市场...\n")

arb_count = 0
scanned = 0

for market in markets:
    question = market.get('question', '无')
    outcome_prices_raw = market.get('outcomePrices', None)
    volume = float(market.get('volume') or 0)

    if not outcome_prices_raw:
        continue

    # 关键修复：字符串转成真正的列表
    try:
        outcome_prices = json.loads(outcome_prices_raw)
    except:
        continue

    if len(outcome_prices) != 2:
        continue

    try:
        yes_price = float(outcome_prices[0])
        no_price = float(outcome_prices[1])
    except:
        continue

    if yes_price == 0 and no_price == 0:
        continue

    scanned += 1
    total = yes_price + no_price

    if total < 0.97:
        profit = round((1 - total) * 100, 2)
        print(f"🚨 套利机会！")
        print(f"   市场: {question}")
        print(f"   YES: ${yes_price}  NO: ${no_price}")
        print(f"   合计: ${total:.4f}  利润: {profit}%")
        print(f"   交易量: ${volume:,.0f}")
        print()
        arb_count += 1
    else:
        print(f"✅ {question[:45]}... 合计: ${total:.4f}")

print(f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print(f"有效扫描: {scanned} 个，套利机会: {arb_count} 个")
