import requests
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

print(f"Token 前10位: {TOKEN[:10] if TOKEN else '没有读取到'}")
print(f"Chat ID: {CHAT_ID}")

# 直接发送测试
url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
data = {"chat_id": CHAT_ID, "text": "测试消息"}
response = requests.post(url, data=data)
print(f"返回结果: {response.json()}")