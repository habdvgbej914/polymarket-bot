import requests
import json
import os
import time
from datetime import datetime
from dotenv import load_dotenv
import anthropic

# 加载 API Key
load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def get_markets(limit=50):
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

def check_simple_arb(markets):
    """检测简单套利机会（市场内）"""
    opportunities = []
    for m in markets:
        if m['total'] < 0.97:
            profit = round((1 - m['total']) * 100, 2)
            opportunities.append({
                'type': '市场内套利',
                'question': m['question'],
                'yes': m['yes'],
                'no': m['no'],
                'profit': profit
            })
    return opportunities

def check_ai_arb(markets):
    """用 AI 检测跨市场套利机会"""
    market_list = ""
    for i, m in enumerate(markets[:30]):  # 只传前30个给AI节省费用
        market_list += f"{i+1}. {m['question']} (YES=${m['yes']})\n"
    
    prompt = f"""你是套利分析师。分析以下Polymarket市场，找出价格矛盾的相关市场对。

{market_list}

只输出发现的套利机会，格式：
[市场编号A] vs [市场编号B]: [一句话说明矛盾] | 建议: [买哪个]

如果没有发现明显机会，输出：无明显跨市场套利机会"""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text

def save_opportunity(text):
    """把套利机会保存到文件"""
    with open("opportunities.txt", "a") as f:
        f.write(text + "\n")

def scan_once(scan_number):
    """执行一次完整扫描"""
    now = datetime.now().strftime("%H:%M:%S")
    print(f"\n{'━'*40}")
    print(f"🔍 第 {scan_number} 次扫描 | 时间: {now}")
    print(f"{'━'*40}")
    
    # 获取市场
    markets = get_markets(50)
    print(f"📊 获取到 {len(markets)} 个市场")
    
    # 检测简单套利
    simple_opps = check_simple_arb(markets)
    if simple_opps:
        for opp in simple_opps:
            msg = f"🚨 市场内套利: {opp['question']} | 利润: {opp['profit']}%"
            print(msg)
            save_opportunity(f"[{datetime.now()}] {msg}")
    else:
        print("✅ 无市场内套利机会")
    
    # 每3次扫描用一次AI（节省费用）
    if scan_number % 3 == 1:
        print("🤖 AI 分析中...")
        ai_result = check_ai_arb(markets)
        print(f"AI结果: {ai_result}")
        
        if "无明显" not in ai_result:
            save_opportunity(f"[{datetime.now()}] AI发现: {ai_result}")
    
    print(f"⏰ 下次扫描: 5分钟后")

# 主循环
print("🚀 自动套利扫描器启动！")
print("按 Control+C 可以停止\n")

scan_number = 1
while True:
    try:
        scan_once(scan_number)
        scan_number += 1
        time.sleep(300)  # 每5分钟扫描一次
        
    except KeyboardInterrupt:
        print("\n\n⛔ 扫描器已停止")
        break
    except Exception as e:
        print(f"⚠️ 出错了: {e}，60秒后重试...")
        time.sleep(60)
