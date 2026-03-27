import requests
import json
from datetime import datetime, timedelta

def get_closed_finance_markets(limit=50):
    """获取已关闭的金融类市场"""
    url = f"https://gamma-api.polymarket.com/markets?active=false&closed=true&limit={limit}&order=volume&ascending=false"
    r = requests.get(url)
    data = r.json()
    
    finance_keywords = ['bitcoin', 'btc', 'ethereum', 'eth', 'price', 'stock', 
                        'fed', 'rate', 'gdp', 'inflation', 'nasdaq', 'tesla', 
                        'apple', 'dollar', 'oil', 'gold', 'xrp', 'crypto']
    
    results = []
    for m in data:
        q = m.get('question', '').lower()
        if any(k in q for k in finance_keywords):
            # 获取最终结果
            prices = json.loads(m.get('outcomePrices', '[]'))
            if len(prices) == 2:
                final_result = 'YES' if float(prices[0]) > 0.5 else 'NO'
                results.append({
                    'question': m.get('question'),
                    'final_result': final_result,
                    'final_yes_price': float(prices[0]),
                    'end_date': m.get('endDate'),
                    'volume': m.get('volumeNum', 0),
                    'clob_token_ids': json.loads(m.get('clobTokenIds', '[]'))
                })
    return results

def get_price_before_close(token_id: str, end_date: str, days_before: int = 7) -> float:
    """获取市场关闭前N天的价格"""
    try:
        end_dt = datetime.fromisoformat(end_date.replace('Z', ''))
        start_dt = end_dt - timedelta(days=days_before)
        mid_dt = start_dt + timedelta(days=1)
        
        start_ts = int(start_dt.timestamp())
        end_ts = int(mid_dt.timestamp())
        
        url = f"https://clob.polymarket.com/prices-history?market={token_id}&startTs={start_ts}&endTs={end_ts}&interval=1d&fidelity=60"
        r = requests.get(url)
        data = r.json()
        
        history = data.get('history', [])
        if history:
            return history[0]['p']
        return None
    except:
        return None

def analyze_accuracy():
    """分析市场预测准确性"""
    print("📊 获取已关闭的金融市场...\n")
    markets = get_closed_finance_markets()
    print(f"找到 {len(markets)} 个金融类市场\n")
    
    results = []
    for m in markets:
        if not m['clob_token_ids']:
            continue
            
        token_id = m['clob_token_ids'][0]
        price_7d = get_price_before_close(token_id, m['end_date'], days_before=7)
        
        if price_7d is None:
            continue
        
        # 市场预测：价格>0.5认为预测YES
        market_prediction = 'YES' if price_7d > 0.5 else 'NO'
        correct = market_prediction == m['final_result']
        
        results.append({
            'question': m['question'][:60],
            'price_7d_before': round(price_7d, 3),
            'market_prediction': market_prediction,
            'final_result': m['final_result'],
            'correct': correct
        })
        
        status = '✅' if correct else '❌'
        print(f"{status} {m['question'][:55]}...")
        print(f"   7天前价格: {price_7d:.3f} → 预测: {market_prediction} → 实际: {m['final_result']}\n")
    
    if results:
        accuracy = sum(1 for r in results if r['correct']) / len(results)
        print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"📈 分析完成")
        print(f"样本数量：{len(results)}")
        print(f"预测准确率：{accuracy*100:.1f}%")
        
        # 分析系统性偏差
        yes_predictions = [r for r in results if r['market_prediction'] == 'YES']
        no_predictions = [r for r in results if r['market_prediction'] == 'NO']
        
        if yes_predictions:
            yes_accuracy = sum(1 for r in yes_predictions if r['correct']) / len(yes_predictions)
            print(f"看多预测准确率：{yes_accuracy*100:.1f}% ({len(yes_predictions)}个样本)")
        
        if no_predictions:
            no_accuracy = sum(1 for r in no_predictions if r['correct']) / len(no_predictions)
            print(f"看空预测准确率：{no_accuracy*100:.1f}% ({len(no_predictions)}个样本)")

if __name__ == "__main__":
    analyze_accuracy()
