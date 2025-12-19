from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import yfinance as yf
import re

app = FastAPI(title="TruthLens AI Backend", version="2.0")

# Allow CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# Data Models
# -----------------------------
class NewsRequest(BaseModel):
    text: str

class StockRequest(BaseModel):
    symbol: str

class ClimateRequest(BaseModel):
    city: str


# -----------------------------
# Utility Functions
# -----------------------------
def clean_text(text):
    """Remove special characters for cleaner search queries."""
    return re.sub(r"[^a-zA-Z0-9\s]", "", text).lower().strip()

def verify_news(text: str):
    """Use NewsData.io API to verify news credibility."""
    try:
        api_key = "pub_739fa9147f314eb385c6eb424899e969"  # ✅ Free public key
        query = clean_text(text)
        url = f"https://newsdata.io/api/1/news?apikey={api_key}&q={query}&language=en"

        response = requests.get(url)
        data = response.json()

        # Validate structure
        if not isinstance(data, dict):
            raise ValueError("Invalid API response structure")

        articles = data.get("results", [])
        if not articles or not isinstance(articles, list):
            return {
                "prediction": "Unknown",
                "confidence": 0,
                "verdict": "No reliable sources found."
            }

        credibility = 0
        trusted_sources = ["bbc", "reuters", "cnn", "ndtv", "indiatimes", "thehindu", "aljazeera"]

        for item in articles:
            if isinstance(item, dict):
                source = str(item.get("source_id", "")).lower()
                title = str(item.get("title", "")).lower()

                if any(t in source for t in trusted_sources):
                    credibility += 20
                elif any(t in title for t in trusted_sources):
                    credibility += 10
                else:
                    credibility += 3

        confidence = min(100, credibility)
        prediction = "True" if confidence >= 50 else "False"

        return {
            "prediction": prediction,
            "confidence": confidence,
            "verdict": f"The statement is likely {prediction} ({confidence}% confidence).",
            "sources": [
                str(a.get("source_id", "unknown")) for a in articles if isinstance(a, dict)
            ][:5],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Verification error: {str(e)}")


# -----------------------------
# Routes
# -----------------------------
@app.post("/analyze-news")
def analyze_news(request: NewsRequest):
    """Analyze and verify news text."""
    result = verify_news(request.text)
    return result


@app.get("/stock")
def get_stock_data(symbol: str):
    """Fetch live stock data using Yahoo Finance."""
    try:
        stock = yf.Ticker(symbol)
        data = stock.history(period="1d")

        if data.empty:
            raise ValueError("Invalid stock symbol or no data available")

        price = float(data["Close"].iloc[-1])
        previous = float(data["Open"].iloc[-1])
        change = ((price - previous) / previous) * 100
        trend = "📈 Rising" if change > 0 else "📉 Falling"

        return {
            "symbol": symbol.upper(),
            "price": round(price, 2),
            "change": round(change, 2),
            "trend": trend,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stock fetch error: {str(e)}")


# -----------------------------
# Weather endpoint (Improved)
# -----------------------------
@app.get("/weather")
def get_weather(city: str):
    """Fetch live weather using Open-Meteo with readable conditions and correct humidity."""
    try:
        # Step 1: Get lat/lon from geocoding
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}"
        geo_res = requests.get(geo_url).json()

        if "results" not in geo_res or not geo_res["results"]:
            raise ValueError("City not found")

        lat = geo_res["results"][0]["latitude"]
        lon = geo_res["results"][0]["longitude"]

        # Step 2: Get weather details
        weather_url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat}&longitude={lon}&current_weather=true&hourly=relativehumidity_2m"
        )
        weather_res = requests.get(weather_url).json()

        current = weather_res.get("current_weather", {})
        humidity_list = weather_res.get("hourly", {}).get("relativehumidity_2m", [])

        # -----------------------
        # Weather Code Mapping
        # -----------------------
        weather_code_map = {
            0: "Clear sky",
            1: "Mainly clear",
            2: "Partly cloudy",
            3: "Overcast",
            45: "Foggy",
            48: "Depositing rime fog",
            51: "Light drizzle",
            53: "Moderate drizzle",
            55: "Dense drizzle",
            61: "Slight rain",
            63: "Moderate rain",
            65: "Heavy rain",
            71: "Slight snow fall",
            73: "Moderate snow fall",
            75: "Heavy snow fall",
            80: "Rain showers",
            81: "Moderate rain showers",
            82: "Violent rain showers",
            95: "Thunderstorm",
            99: "Thunderstorm with hail",
        }

        weather_code = current.get("weathercode", None)
        condition = weather_code_map.get(weather_code, "Unknown")

        humidity = humidity_list[0] if humidity_list else "N/A"

        return {
            "city": city.title(),
            "temperature": current.get("temperature", "N/A"),
            "condition": condition,
            "humidity": humidity,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Weather fetch error: {str(e)}")



@app.get("/")
def home():
    return {"message": "✅ TruthLens Backend is Running"}


# -----------------------------
# Run Command
# -----------------------------
# Run using:
# uvicorn main:app --reload
