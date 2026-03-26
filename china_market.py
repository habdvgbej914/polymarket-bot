import requests
import os
from dotenv import load_dotenv
import anthropic
from datetime import datetime

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
FINNHUB_KEY = os.getenv("FINNHUB_API_KEY")

# 关注的A股相关关键词
TOPICS = ["China", "Chinese", "Beijing", "tariff", "trade war", "yuan", "renminbi", "Hong Kong", "Alibaba", "Tencent", "BYD", "Huawei"]


def get_china_news():
    """从Finnhub抓取中国市场相关新闻"""
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
                "summary": news.get("summary", "")[:200],
                "datetime": news.get("datetime")
            })
    
    return filtered[:10]

def analyze_with_ai(news_list):
    """用Claude分析新闻情绪和市场影响"""
    
    if not news_list:
        return "今日暂无相关新闻。"
    
    news_text = ""
    for i, n in enumerate(news_list):
        news_text += f"{i+1}. {n['headline']}\n{n['summary']}\n\n"
    
    prompt = f"""你是一个A股市场分析师。以下是今日相关财经新闻：

{news_text}

请完成以下分析：
1. 整体市场情绪：看多/看空/中性
2. 最值得关注的1-2条新闻及原因
3. 对A股短期影响的简要判断

用简洁的中文回答，总字数不超过300字。"""

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=600,
        messages=[{"role": "user", "content": prompt}]
    )
    
    return message.content[0].text

def send_telegram(text):
    """发送Telegram通知"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    }
    requests.post(url, json=payload)

# 主程序
print("📰 正在抓取中国市场新闻...")
news = get_china_news()
print(f"找到 {len(news)} 条相关新闻\n")

print("🤖 正在用AI分析...")
analysis = analyze_with_ai(news)

now = datetime.now().strftime("%Y-%m-%d %H:%M")
message = f"""📊 *A股每日简报* {now}

{analysis}

---
_数据来源：Finnhub | 分析：Claude AI_"""

print(message)
send_telegram(message)
print("\n✅ 已发送到Telegram")


