import requests, os
from dotenv import load_dotenv
load_dotenv()

NEWS_API_KEY = os.getenv("NEWS_API_KEY")

def get_live_news():
    url = f"https://newsapi.org/v2/top-headlines?language=en&pageSize=5&apiKey={NEWS_API_KEY}"
    resp = requests.get(url)
    data = resp.json()
    articles = data.get("articles", [])
    news_list = []

    for a in articles:
        news_list.append({
            "title": a["title"],
            "description": a["description"] or "",
            "url": a["url"]
        })
    return news_list
