import requests
import os
import json
from datetime import datetime
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv()

FINNHUB_KEY = os.getenv("FINNHUB_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
HISTORY_FILE = "/Users/sese/Desktop/polymarket-bot/market_history.json"

TOPICS = ["China", "Chinese", "Beijing", "tariff", "trade war", 
          "yuan", "renminbi", "Hong Kong", "Alibaba", "Tencent", "BYD", "Huawei"]

app = FastMCP("china-market-server")

def load_history():
    try:
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    except:
        return {"bullish": 0.33, "bearish": 0.33, "neutral": 0.34, "history": []}

def save_history(data):
    with open(HISTORY_FILE, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def bayesian_update(prior: dict, sentiment: str) -> dict:
    likelihood = {
        "bullish":  {"bullish": 0.7, "bearish": 0.1, "neutral": 0.2},
        "bearish":  {"bullish": 0.1, "bearish": 0.7, "neutral": 0.2},
        "neutral":  {"bullish": 0.3, "bearish": 0.3, "neutral": 0.4}
    }
    if sentiment not in likelihood:
        return prior
    posterior = {}
    total = 0
    for state in ["bullish", "bearish", "neutral"]:
        posterior[state] = prior[state] * likelihood[sentiment][state]
        total += posterior[state]
    for state in posterior:
        posterior[state] = round(posterior[state] / total, 3)
    return posterior

def calculate_confidence_interval(probability: float, history: list) -> dict:
    """
    计算情绪概率的95%置信区间
    公式：均值 ± 1.96 × 标准差
    
    参数：
    - probability: 当前贝叶斯概率
    - history: 历史概率记录列表
    """
    import statistics
    
    if len(history) < 2:
        return {
            "mean": probability,
            "lower": max(0, probability - 0.1),
            "upper": min(1, probability + 0.1),
            "note": "历史数据不足，使用默认区间±10%"
        }
    
    # 提取历史看多概率
    historical_probs = [h["posterior"]["bullish"] for h in history]
    
    mean = statistics.mean(historical_probs)
    std_dev = statistics.stdev(historical_probs)
    
    # 95%置信区间
    margin = 1.96 * std_dev
    lower = max(0, mean - margin)
    upper = min(1, mean + margin)
    
    return {
        "mean": round(mean, 3),
        "std_dev": round(std_dev, 3),
        "lower": round(lower, 3),
        "upper": round(upper, 3),
        "note": f"基于{len(historical_probs)}个交易日数据"
    }

def calculate_sharpe(returns: list, risk_free_rate: float = 0.02) -> dict:
    """
    计算夏普比率
    公式：(平均收益率 - 无风险利率) / 收益率标准差
    
    参数：
    - returns: 每日收益率列表（例如 [0.01, -0.02, 0.03]）
    - risk_free_rate: 年化无风险利率，默认2%（中国国债利率参考）
    """
    if len(returns) < 2:
        return {"error": "数据不足，至少需要2个交易日数据"}
    
    import statistics
    
    # 日均收益率
    avg_return = sum(returns) / len(returns)
    
    # 收益率标准差（风险）
    std_dev = statistics.stdev(returns)
    
    if std_dev == 0:
        return {"error": "标准差为零，无法计算"}
    
    # 转换为日化无风险利率
    daily_risk_free = risk_free_rate / 252
    
    # 夏普比率（年化）
    sharpe = (avg_return - daily_risk_free) / std_dev * (252 ** 0.5)
    
    return {
        "sharpe_ratio": round(sharpe, 3),
        "avg_daily_return": round(avg_return * 100, 3),
        "std_dev": round(std_dev * 100, 3),
        "interpretation": "优秀" if sharpe > 1 else "良好" if sharpe > 0.5 else "较差"
    }

@app.tool()
def get_china_news() -> str:
    """从Finnhub抓取中国市场相关财经新闻"""
    url = f"https://finnhub.io/api/v1/news?category=general&token={FINNHUB_KEY}"
    response = requests.get(url)
    all_news = response.json()
    filtered = []
    for news in all_news:
        headline = news.get("headline", "").lower()
        summary = news.get("summary", "").lower()
        if any(topic.lower() in headline or topic.lower() in summary for topic in TOPICS):
            filtered.append({
                "headline": news.get("headline"),
                "summary": news.get("summary", "")[:200]
            })
    if not filtered:
        return "今日暂无相关新闻"
    result = ""
    for i, n in enumerate(filtered[:10]):
        result += f"{i+1}. {n['headline']}\n{n['summary']}\n\n"
    return result

@app.tool()
def get_sharpe_ratio(symbol: str = "BABA") -> str:
    """
    计算指定股票的夏普比率
    目前使用模拟数据，回国后接入AKShare替换真实数据
    symbol参数：股票代码，例如BABA、BIDU、JD
    """
    # 占位数据，回国后替换为AKShare真实历史价格
    mock_returns = [0.01, -0.02, 0.03, -0.01, 0.02, 
                    0.015, -0.005, 0.02, -0.03, 0.01,
                    0.008, -0.012, 0.025, -0.008, 0.018,
                    0.003, -0.015, 0.022, -0.006, 0.011,
                    0.009, -0.018, 0.014, -0.004, 0.019,
                    0.007, -0.009, 0.016, -0.011, 0.013]
    
    result = calculate_sharpe(mock_returns)
    
    if "error" in result:
        return result["error"]
    
    return f"""
{symbol} 夏普比率分析：
夏普比率：{result['sharpe_ratio']}
日均收益率：{result['avg_daily_return']}%
收益波动率（标准差）：{result['std_dev']}%
评级：{result['interpretation']}

注：当前使用模拟数据，回国后接入AKShare真实数据
"""

@app.tool()
def get_pe_analysis(symbol: str = "BABA") -> str:
    """
    获取股票市盈率(PE)及估值分析
    symbol参数：股票代码，例如BABA、BIDU、JD
    """
    # 获取财务指标
    url = f"https://finnhub.io/api/v1/stock/metric?symbol={symbol}&metric=all&token={FINNHUB_KEY}"
    response = requests.get(url)
    data = response.json().get("metric", {})
    
    # 获取当前价格
    quote_url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_KEY}"
    quote = requests.get(quote_url).json()
    
    current_price = quote.get("c", 0)
    eps_annual = data.get("epsAnnual", 0)
    eps_ttm = data.get("epsInclExtraItemsTTM", 0)
    pe_ttm = current_price / eps_ttm if eps_ttm > 0 else None
    pe_annual = current_price / eps_annual if eps_annual > 0 else None
    
    # PE估值判断
    def pe_interpretation(pe):
        if pe is None:
            return "无法计算"
        elif pe < 10:
            return "低估（<10倍）"
        elif pe < 20:
            return "合理（10-20倍）"
        elif pe < 30:
            return "偏高（20-30倍）"
        else:
            return "高估（>30倍）"
    
    return f"""
{symbol} 市盈率(PE)分析：
当前价格：${current_price}
每股收益(EPS年度)：${eps_annual}
每股收益(EPS TTM)：${eps_ttm}

市盈率(年度PE)：{round(pe_annual, 2) if pe_annual else 'N/A'}倍
市盈率(TTM PE)：{round(pe_ttm, 2) if pe_ttm else 'N/A'}倍

估值判断：{pe_interpretation(pe_ttm)}

52周最高：${data.get('52WeekHigh', 'N/A')}
52周最低：${data.get('52WeekLow', 'N/A')}
Beta系数：{data.get('beta', 'N/A')}
"""

@app.tool()
def get_sentiment_confidence() -> str:
    """
    获取市场情绪的95%置信区间
    基于历史贝叶斯数据计算正态分布置信区间
    """
    history = load_history()
    current_prob = history["bullish"]
    historical_records = history.get("history", [])
    
    ci = calculate_confidence_interval(current_prob, historical_records)
    
    return f"""
市场情绪置信区间分析：

当前看多概率：{current_prob*100:.1f}%
95%置信区间：[{ci['lower']*100:.1f}%, {ci['upper']*100:.1f}%]

解读：
我们有95%的把握认为，市场真实看多概率在{ci['lower']*100:.1f}%到{ci['upper']*100:.1f}%之间。

{ci['note']}
标准差：{ci.get('std_dev', 'N/A')}
"""

@app.tool()
def update_market_sentiment(sentiment: str) -> str:
    """用贝叶斯公式更新市场情绪概率，sentiment参数：bullish/bearish/neutral"""
    history = load_history()
    prior = {
        "bullish": history["bullish"],
        "bearish": history["bearish"],
        "neutral": history["neutral"]
    }
    posterior = bayesian_update(prior, sentiment)
    history["bullish"] = posterior["bullish"]
    history["bearish"] = posterior["bearish"]
    history["neutral"] = posterior["neutral"]
    history["history"].append({
        "date": datetime.now().strftime("%Y-%m-%d"),
        "sentiment": sentiment,
        "posterior": posterior
    })
    save_history(history)
    return f"""贝叶斯情绪更新完成：
今日信号：{sentiment}
更新后概率：
  看多(Bullish)：{posterior['bullish']*100:.1f}%
  看空(Bearish)：{posterior['bearish']*100:.1f}%
  中性(Neutral)：{posterior['neutral']*100:.1f}%"""

@app.tool()
def send_telegram(message: str) -> str:
    """发送消息到Telegram"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        return "消息发送成功"
    return f"发送失败: {response.status_code}"

@app.resource("market://daily-brief")
def get_daily_brief() -> str:
    """今日A股市场简报资源"""
    news = get_china_news()
    history = load_history()
    return f"""今日市场数据：
{news}
当前贝叶斯概率：
  看多：{history['bullish']*100:.1f}%
  看空：{history['bearish']*100:.1f}%
  中性：{history['neutral']*100:.1f}%"""

@app.prompt("analyze-market")
def analyze_market_prompt() -> str:
    """A股市场分析的标准提示词模板"""
    history = load_history()
    return f"""你是一个专业的A股市场分析师，请按以下框架分析今日市场：

当前贝叶斯先验概率：
  看多：{history['bullish']*100:.1f}%
  看空：{history['bearish']*100:.1f}%
  中性：{history['neutral']*100:.1f}%

请完成以下分析：
1. 整体情绪判断：看多/看空/中性，并说明理由
2. 贝叶斯更新：今日新闻如何改变上述先验概率
3. 核心驱动因素：最重要的1-2个新闻事件
4. 风险提示：需要警惕的潜在风险
5. 建议关注板块：具体说明原因

分析完成后，请调用update_market_sentiment工具更新概率。
请用简洁专业的中文回答，总字数不超过400字。"""

if __name__ == "__main__":
    app.run()