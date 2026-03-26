import requests
import os
import time
import re
from datetime import datetime
from dotenv import load_dotenv
import anthropic

load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
FINNHUB_KEY = os.getenv("FINNHUB_API_KEY")

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        requests.post(url, data=data)
    except:
        pass

def get_finnhub_news():
    headlines = []
    categories = ["general", "crypto", "forex"]
    for cat in categories:
        try:
            r = requests.get(
                "https://finnhub.io/api/v1/news?category=" + cat + "&token=" + FINNHUB_KEY,
                timeout=5
            )
            data = r.json()
            for item in data[:5]:
                headline = item.get("headline", "")
                if headline:
                    headlines.append("[" + cat.upper() + "] " + headline)
        except:
            continue
    return headlines[:20]

def get_reuters_news():
    headlines = []
    feeds = [
        "https://feeds.reuters.com/reuters/topNews",
        "https://feeds.reuters.com/reuters/businessNews",
    ]
    for feed_url in feeds:
        try:
            r = requests.get(feed_url, timeout=5)
            titles = re.findall(r"<title>(.*?)</title>", r.text)
            for title in titles[2:6]:
                clean = re.sub(r"<[^>]+>", "", title).strip()
                if clean and len(clean) > 10:
                    headlines.append("[REUTERS] " + clean)
        except:
            continue
    return headlines

def get_polymarket_questions():
    url = "https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=50&order=volume&ascending=false"
    response = requests.get(url)
    markets = response.json()
    return [m.get("question", "") for m in markets if m.get("question")]

def analyze_news_vs_markets(headlines, market_questions):
    headlines_text = "\n".join(["- " + h for h in headlines])
    markets_text = "\n".join([str(i+1) + ". " + q for i, q in enumerate(market_questions[:30])])

    prompt = "You are a prediction market trader.\n\n"
    prompt += "Latest financial news:\n" + headlines_text + "\n\n"
    prompt += "Current Polymarket markets:\n" + markets_text + "\n\n"
    prompt += "Find news that could affect market prices before the market reacts.\n"
    prompt += "Only output real impacts using this format:\n"
    prompt += "News: [title]\n"
    prompt += "Market: [number and name]\n"
    prompt += "Impact: [price goes up or down, why]\n"
    prompt += "Urgency: [now / today / this week]\n\n"
    prompt += "If no clear impact found, output: no news impact found"

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text

def scan_news(scan_number):
    now = datetime.now().strftime("%H:%M:%S")
    print("")
    print("=" * 40)
    print("News Scan #" + str(scan_number) + " | " + now)
    print("=" * 40)

    finnhub_news = get_finnhub_news()
    reuters_news = get_reuters_news()
    all_headlines = finnhub_news + reuters_news

    print("Finnhub: " + str(len(finnhub_news)) + " articles")
    print("Reuters: " + str(len(reuters_news)) + " articles")
    print("Total: " + str(len(all_headlines)) + " articles\n")

    if not all_headlines:
        print("No news found")
        return

    markets = get_polymarket_questions()
    print("Markets: " + str(len(markets)) + "\n")

    print("AI analyzing...")
    result = analyze_news_vs_markets(all_headlines, markets)
    print(result)

    if "no news impact found" not in result.lower():
        msg = "<b>News Arbitrage Opportunity!</b>\n\n" + result
        send_telegram(msg)
        print("Telegram notification sent!")
        with open("news_opportunities.txt", "a") as f:
            f.write("\n[" + str(datetime.now()) + "]\n" + result + "\n")

print("News Scanner Started (Finnhub + Reuters)")
print("Press Control+C to stop\n")

scan_number = 1
while True:
    try:
        scan_news(scan_number)
        scan_number += 1
        print("\nNext scan in 2 hours...")
        time.sleep(7200)
    except KeyboardInterrupt:
        print("\nStopped")
        break
    except Exception as e:
        print("Error: " + str(e) + ", retrying in 60s...")
        time.sleep(60)