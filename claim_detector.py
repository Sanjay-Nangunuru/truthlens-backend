import os
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def extract_claims(text):
    prompt = f"""
    You are a fact-check claim detector.
    Extract all factual claims (concise sentences) from this text:
    "{text}"
    Return a Python list of strings.
    """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"user", "content":prompt}]
    )
    claims_text = response.choices[0].message.content
    try:
        claims = eval(claims_text)
    except:
        claims = [text]
    return claims
