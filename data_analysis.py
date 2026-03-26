import requests
import json
import os
from datetime import datetime
from dotenv import load_dotenv
import anthropic

load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def get_large_sample(limit=200):
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
            total = yes_price + no_price
            spread = abs(total - 1.0)
            result.append({
                'question': market.get('question'),
                'yes': yes_price,
                'no': no_price,
                'total': round(total, 4),
                'spread': round(spread, 4),
                'volume': float(market.get('volume') or 0),
            })
        except:
            continue
    return result

def categorize_market(question):
    question = question.lower()
    if any(w in question for w in ['temperature', 'weather', 'rain', 'celsius', 'fahrenheit']):
        return '天气'
    elif any(w in question for w in ['bitcoin', 'btc', 'ethereum', 'eth', 'solana', 'crypto']):
        return '加密货币'
    elif any(w in question for w in ['election', 'president', 'senate', 'congress', 'vote']):
        return '政治选举'
    elif any(w in question for w in ['trump', 'biden', 'elon', 'musk', 'zelensky', 'putin']):
        return '政治人物'
    elif any(w in question for w in ['nba', 'nfl', 'mlb', 'nhl', 'football', 'basketball', 'tennis', 'ufc']):
        return '体育'
    elif any(w in question for w in ['stock', 'nasdaq', 'apple', 'nvidia', 'tesla', 'amazon']):
        return '股票'
    elif any(w in question for w in ['war', 'ukraine', 'russia', 'israel', 'iran', 'china']):
        return '地缘政治'
    elif any(w in question for w in ['fed', 'rate', 'inflation', 'gdp', 'economy']):
        return '经济'
    else:
        return '其他'

def analyze_by_category(markets):
    categories = {}
    for m in markets:
        cat = categorize_market(m['question'])
        if cat not in categories:
            categories[cat] = {
                'count': 0,
                'spreads': [],
                'volumes': [],
                'examples': []
            }
        categories[cat]['count'] += 1
        categories[cat]['spreads'].append(m['spread'])
        categories[cat]['volumes'].append(m['volume'])
        if m['spread'] > 0.02:
            categories[cat]['examples'].append(m)
    for cat in categories:
        spreads = categories[cat]['spreads']
        volumes = categories[cat]['volumes']
        categories[cat]['avg_spread'] = round(sum(spreads) / len(spreads), 4)
        categories[cat]['max_spread'] = round(max(spreads), 4)
        categories[cat]['avg_volume'] = round(sum(volumes) / len(volumes), 2)
    return categories

def print_report(categories, markets):
    print("\n" + "="*50)
    print("市场类别分析报告")
    print("="*50)
    sorted_cats = sorted(categories.items(), key=lambda x: x[1]['avg_spread'], reverse=True)
    print(f"\n{'类别':<10} {'数量':>5} {'平均价差':>10} {'最大价差':>10} {'平均交易量':>12}")
    print("-"*50)
    for cat, data in sorted_cats:
        print(f"{cat:<10} {data['count']:>5} {data['avg_spread']:>10.4f} {data['max_spread']:>10.4f} ${data['avg_volume']:>11,.0f}")
    print("\n最佳套利狩猎场（按价差排序）：")
    for i, (cat, data) in enumerate(sorted_cats[:3]):
        print(f"\n#{i+1} {cat}")
        print(f"   平均价差: {data['avg_spread']*100:.2f}%")
        print(f"   最大价差: {data['max_spread']*100:.2f}%")
        print(f"   平均交易量: ${data['avg_volume']:,.0f}")
        if data['examples']:
            print(f"   高价差例子:")
            for ex in data['examples'][:2]:
                print(f"   - {ex['question'][:50]}")
                print(f"     价差: {ex['spread']*100:.2f}%, 交易量: ${ex['volume']:,.0f}")
    all_spreads = [m['spread'] for m in markets]
    print("\n总体统计")
    print(f"扫描市场总数: {len(markets)}")
    print(f"平均价差: {sum(all_spreads)/len(all_spreads)*100:.3f}%")
    print(f"价差>2%: {sum(1 for s in all_spreads if s > 0.02)} 个")
    print(f"价差>3%: {sum(1 for s in all_spreads if s > 0.03)} 个")

def ai_strategy_advice(categories):
    summary = ""
    for cat, data in categories.items():
        line = cat + ": 数量=" + str(data['count'])
        line += ", 平均价差=" + str(round(data['avg_spread']*100, 2)) + "%"
        line += ", 平均交易量=$" + str(int(data['avg_volume']))
        summary += line + "\n"
    
    prompt = "以下是Polymarket各类市场统计数据:\n" + summary
    prompt += "\n根据这些数据给出：1.最值得关注的类别和原因 2.应该避开的类别和原因 3.具体套利策略建议。请用简洁中文回答。"

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=600,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text

# 主程序
print("数据分析启动...")
print("获取200个市场数据中...\n")
markets = get_large_sample(200)
print(f"成功获取 {len(markets)} 个有效市场\n")
categories = analyze_by_category(markets)
print_report(categories, markets)
print("\nAI策略建议")
print("="*50)
ai_advice = ai_strategy_advice(categories)
print(ai_advice)

with open("analysis_report.txt", "w") as f:
    f.write("分析时间: " + str(datetime.now()) + "\n")
    f.write("市场数量: " + str(len(markets)) + "\n\n")
    for cat, data in categories.items():
        f.write(cat + ": " + str(data) + "\n")
    f.write("\nAI建议:\n" + ai_advice + "\n")

print("\n报告已保存到 analysis_report.txt")