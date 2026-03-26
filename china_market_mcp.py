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

@app.prompt("analyze-market")
def analyze_market_prompt() -> str:
    """A股市场分析的标准提示词模板"""
    return """你是一个专业的A股市场分析师，请按以下框架分析今日市场：

1. 整体情绪：看多/看空/中性，给出置信度百分比
2. 核心驱动因素：列出最重要的1-2个新闻事件
3. 贝叶斯更新：基于今日新闻，市场情绪较昨日有何变化
4. 风险提示：需要警惕的潜在风险
5. 建议关注板块：具体说明原因

请用简洁专业的中文回答，总字数不超过400字。"""

if __name__ == "__main__":
    app.run()
