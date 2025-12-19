import requests, os
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
BING_API_KEY = os.getenv("BING_API_KEY")

def bing_search(query):
    url = "https://api.bing.microsoft.com/v7.0/search"
    headers = {"Ocp-Apim-Subscription-Key": BING_API_KEY}
    params = {"q": query, "count": 3, "mkt": "en-IN"}
    r = requests.get(url, headers=headers, params=params)
    data = r.json()
    results = []
    for item in data.get("webPages", {}).get("value", []):
        results.append({
            "name": item["name"],
            "snippet": item["snippet"],
            "url": item["url"]
        })
    return results

def verify_claims(claim):
    evidence = bing_search(claim)
    context = "\n".join([f"{e['name']}: {e['snippet']} ({e['url']})" for e in evidence])
    prompt = f"""
    You are a real-time misinformation detector.
    Analyze the following claim based on live evidence.

    Claim: "{claim}"
    Evidence:
    {context}

    Answer strictly in JSON:
    {{
        "verdict": "Supported" or "Refuted" or "Unverified",
        "confidence": number between 0 and 1,
        "explanation": "short reasoning (2 lines)",
        "sources": [list of URLs]
    }}
    """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"user", "content":prompt}]
    )
    return eval(response.choices[0].message.content)
