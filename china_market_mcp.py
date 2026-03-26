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