import requests
import os
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv()

FINNHUB_KEY = os.getenv("FINNHUB_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

TOPICS = ["China", "Chinese", "Beijing", "tariff", "trade war", 
          "yuan", "renminbi", "Hong Kong", "Alibaba", "Tencent", "BYD", "Huawei"]

app = FastMCP("china-market-server")

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
def send_telegram(message: str) -> str:
    """发送消息到Telegram"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        return "消息发送成功"
    return f"发送失败: {response.status_code}"

@app.resource("market://daily-brief")
def get_daily_brief() -> str:
    """今日A股市场简报资源"""
    news = get_china_news()
    return f"今日市场数据：\n{news}"
    
if __name__ == "__main__":
    app.run()