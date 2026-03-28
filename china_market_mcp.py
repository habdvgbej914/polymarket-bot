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

def get_market_factors(symbol: str = "BABA") -> dict:
    """
    获取多因子数据
    返回各因子的信号强度：1=看多, -1=看空, 0=中性
    """
    factors = {}
    
    url = f"https://finnhub.io/api/v1/stock/metric?symbol={symbol}&metric=all&token={FINNHUB_KEY}"
    data = requests.get(url).json().get("metric", {})
    
    quote_url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_KEY}"
    quote = requests.get(quote_url).json()
    
    # 因子1：成交量异常（10日均量 vs 3月均量）
    vol_10d = data.get("10DayAverageTradingVolume", 0)
    vol_3m = data.get("3MonthAverageTradingVolume", 0)
    if vol_3m > 0:
        vol_ratio = vol_10d / vol_3m
        if vol_ratio > 1.2:
            factors["volume"] = {"signal": 1, "value": round(vol_ratio, 2), "note": "成交量放大，看多"}
        elif vol_ratio < 0.8:
            factors["volume"] = {"signal": -1, "value": round(vol_ratio, 2), "note": "成交量萎缩，看空"}
        else:
            factors["volume"] = {"signal": 0, "value": round(vol_ratio, 2), "note": "成交量正常"}
    
    # 因子2：波动率（Beta）
    beta = data.get("beta", 1)
    if beta > 1.5:
        factors["volatility"] = {"signal": -1, "value": beta, "note": "高波动，风险偏高"}
    elif beta < 0.5:
        factors["volatility"] = {"signal": 1, "value": beta, "note": "低波动，相对稳定"}
    else:
        factors["volatility"] = {"signal": 0, "value": beta, "note": "波动正常"}
    
    # 因子3：价格动量（当日涨跌幅）
    change_pct = quote.get("dp", 0)
    if change_pct > 2:
        factors["momentum"] = {"signal": 1, "value": change_pct, "note": f"今日涨{change_pct:.1f}%，动量偏强"}
    elif change_pct < -2:
        factors["momentum"] = {"signal": -1, "value": change_pct, "note": f"今日跌{abs(change_pct):.1f}%，动量偏弱"}
    else:
        factors["momentum"] = {"signal": 0, "value": change_pct, "note": f"今日涨跌{change_pct:.1f}%，动量中性"}
    
    # 因子4：资金流向（占位，回国后接AKShare）
    factors["fund_flow"] = {"signal": 0, "value": None, "note": "待接入真实数据"}
    
    return factors

def multi_factor_bayesian(prior: dict, news_sentiment: str, symbol: str = "BABA") -> dict:
    """
    多因子贝叶斯更新
    权重：新闻情绪40% + 成交量25% + 波动率10% + 动量25%
    """
    weights = {
        "news": 0.40,
        "volume": 0.25,
        "momentum": 0.25,
        "volatility": 0.10
    }
    
    factors = get_market_factors(symbol)
    
    # 新闻情绪映射
    news_signal = 1 if news_sentiment == "bullish" else -1 if news_sentiment == "bearish" else 0
    
    # 计算加权综合信号
    weighted_signal = (
        news_signal * weights["news"] +
        factors.get("volume", {}).get("signal", 0) * weights["volume"] +
        factors.get("momentum", {}).get("signal", 0) * weights["momentum"] +
        factors.get("volatility", {}).get("signal", 0) * weights["volatility"]
    )
    
    # 把综合信号转回sentiment
    if weighted_signal > 0.1:
        combined_sentiment = "bullish"
    elif weighted_signal < -0.1:
        combined_sentiment = "bearish"
    else:
        combined_sentiment = "neutral"
    
    # 用综合情绪做贝叶斯更新
    posterior = bayesian_update(prior, combined_sentiment)
    
    return {
        "posterior": posterior,
        "weighted_signal": round(weighted_signal, 3),
        "factors": factors,
        "combined_sentiment": combined_sentiment
    }

def calculate_confidence_interval(probability: float, history: list) -> dict:
    import statistics
    if len(history) < 2:
        return {
            "mean": probability,
            "lower": max(0, probability - 0.1),
            "upper": min(1, probability + 0.1),
            "note": "历史数据不足，使用默认区间±10%"
        }
    historical_probs = [h["posterior"]["bullish"] for h in history]
    mean = statistics.mean(historical_probs)
    std_dev = statistics.stdev(historical_probs)
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
    if len(returns) < 2:
        return {"error": "数据不足，至少需要2个交易日数据"}
    import statistics
    avg_return = sum(returns) / len(returns)
    std_dev = statistics.stdev(returns)
    if std_dev == 0:
        return {"error": "标准差为零，无法计算"}
    daily_risk_free = risk_free_rate / 252
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
    """计算指定股票的夏普比率，目前使用模拟数据"""
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
    """获取股票市盈率及估值分析"""
    url = f"https://finnhub.io/api/v1/stock/metric?symbol={symbol}&metric=all&token={FINNHUB_KEY}"
    response = requests.get(url)
    data = response.json().get("metric", {})
    quote_url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_KEY}"
    quote = requests.get(quote_url).json()
    current_price = quote.get("c", 0)
    eps_annual = data.get("epsAnnual", 0)
    eps_ttm = data.get("epsInclExtraItemsTTM", 0)
    pe_ttm = current_price / eps_ttm if eps_ttm > 0 else None
    pe_annual = current_price / eps_annual if eps_annual > 0 else None
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
    """获取市场情绪的95%置信区间"""
    history = load_history()
    current_prob = history["bullish"]
    historical_records = history.get("history", [])
    ci = calculate_confidence_interval(current_prob, historical_records)
    return f"""
市场情绪置信区间分析：
当前看多概率：{current_prob*100:.1f}%
95%置信区间：[{ci['lower']*100:.1f}%, {ci['upper']*100:.1f}%]
解读：我们有95%的把握认为，市场真实看多概率在{ci['lower']*100:.1f}%到{ci['upper']*100:.1f}%之间。
{ci['note']}
标准差：{ci.get('std_dev', 'N/A')}
"""

@app.tool()
def get_personalized_analysis() -> str:
    """基于用户画像的个性化投资分析"""
    user_profile = {
        "资金量": "1000英镑",
        "经验": "有实操经验，短线亏损后转向长期",
        "风险偏好": "保本优先，止损设3-5%",
        "目标": "长期增值+学习",
        "周期": "1-3年",
        "市场": "美股为主，关注A股和加密货币"
    }
    history = load_history()
    bullish_prob = history["bullish"]
    if bullish_prob > 0.6:
        action = "市场情绪偏多，符合长期建仓条件"
        suggestion = "可以考虑小仓位（不超过总资金20%）分批建仓"
    elif bullish_prob < 0.4:
        action = "市场情绪偏空，保本优先"
        suggestion = "建议观望，保持现金仓位"
    else:
        action = "市场情绪中性，等待更明确信号"
        suggestion = "继续观察，不急于操作"
    return f"""
🎩 个性化投资分析（高级定制版）
客户画像：
  资金量：{user_profile['资金量']}
  风险偏好：{user_profile['风险偏好']}
  投资目标：{user_profile['目标']}
  投资周期：{user_profile['周期']}
当前市场信号：
  看多概率：{bullish_prob*100:.1f}%
  市场判断：{action}
个性化建议：
  {suggestion}
定制说明：
  基于您保本优先的偏好，任何操作止损设在3-5%
  基于您1-3年周期，关注基本面而非短期波动
  基于您1000英镑资金量，单笔投入不超过200英镑
"""
@app.tool()
def multi_factor_analysis(sentiment: str = "bullish", symbol: str = "BABA") -> str:
    """
    多因子贝叶斯市场分析
    结合新闻情绪、成交量、波动率、价格动量四个因子
    sentiment参数：bullish/bearish/neutral
    symbol参数：股票代码，例如BABA、BIDU、JD
    """
    history = load_history()
    prior = {
        "bullish": history["bullish"],
        "bearish": history["bearish"],
        "neutral": history["neutral"]
    }
    
    result = multi_factor_bayesian(prior, sentiment, symbol)
    factors = result["factors"]
    posterior = result["posterior"]
    
    # 更新历史记录
    history["bullish"] = posterior["bullish"]
    history["bearish"] = posterior["bearish"]
    history["neutral"] = posterior["neutral"]
    history["history"].append({
        "date": datetime.now().strftime("%Y-%m-%d"),
        "sentiment": result["combined_sentiment"],
        "posterior": posterior,
        "factors": {k: v.get("signal") for k, v in factors.items()}
    })
    save_history(history)
    
    return f"""
📊 多因子贝叶斯分析（{symbol}）

因子信号：
  新闻情绪：{sentiment} → 信号: {1 if sentiment=='bullish' else -1 if sentiment=='bearish' else 0}（权重40%）
  成交量：{factors['volume']['note']} → 信号: {factors['volume']['signal']}（权重25%）
  价格动量：{factors['momentum']['note']} → 信号: {factors['momentum']['signal']}（权重25%）
  波动率：{factors['volatility']['note']} → 信号: {factors['volatility']['signal']}（权重10%）
  资金流向：{factors['fund_flow']['note']}（权重0%，待接入）

综合信号：{result['weighted_signal']} → {result['combined_sentiment']}

贝叶斯更新后：
  看多：{posterior['bullish']*100:.1f}%
  看空：{posterior['bearish']*100:.1f}%
  中性：{posterior['neutral']*100:.1f}%
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
def analyze_with_local_model(news_text: str, model: str = "qwen2.5:7b") -> str:
    """
    用本地模型分析市场新闻
    model参数：qwen2.5:7b 或 deepseek-r1:7b
    """
    import ollama
    
    prompt = f"""你是一个A股市场分析师。以下是今日相关财经新闻：

{news_text}

请完成以下分析：
1. 整体市场情绪：看多/看空/中性
2. 最值得关注的1-2条新闻及原因
3. 对A股短期影响的简要判断

用简洁的中文回答，总字数不超过300字。"""

    response = ollama.chat(
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )
    
    return f"""
【{model}本地分析结果】

{response['message']['content']}
"""

@app.tool()
def compare_models() -> str:
    """
    同时用Qwen和DeepSeek分析当前市场新闻，输出对比结果
    """
    import ollama
    
    news_list = get_china_news()
    if not news_list:
        return "今日暂无相关新闻"
    
    news_text = ""
    for i, n in enumerate(news_list):
        news_text += f"{i+1}. {n['headline']}\n{n['summary']}\n\n"
    
    prompt = f"""你是一个A股市场分析师。以下是今日相关财经新闻：

{news_text}

请完成以下分析：
1. 整体市场情绪：看多/看空/中性
2. 最值得关注的新闻
3. 对A股短期影响

用简洁中文回答，不超过200字。"""

    qwen_response = ollama.chat(
        model="qwen2.5:7b",
        messages=[{"role": "user", "content": prompt}]
    )
    
    deepseek_response = ollama.chat(
        model="deepseek-r1:7b",
        messages=[{"role": "user", "content": prompt}]
    )
    
    return f"""
📊 模型对比分析

🔵 Qwen2.5-7B：
{qwen_response['message']['content']}

🔴 DeepSeek-R1-7B：
{deepseek_response['message']['content']}
"""

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