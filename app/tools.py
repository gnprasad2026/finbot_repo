import os
import yfinance as yf
from langchain.tools import tool
from langchain_community.utilities import SerpAPIWrapper
from app.config import settings

from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
from langchain_community.tools.yahoo_finance_news import YahooFinanceNewsTool

GROQ_API_KEY = settings.GROQ_API_KEY
SERP_API_KEY = settings.SERP_API_KEY

print(f" GROQ API KEY : {GROQ_API_KEY}")
print(f" SERP API KEY : {SERP_API_KEY}")


@tool
def get_stock_fundamentals(ticker: str) -> str:
    """Get current stock price, P/E ratio, market cap, and revenue growth for a ticker."""
    stock = yf.Ticker(ticker)
    info = stock.info
    return {
        "price": info.get("currentPrice"),
        "pe_ratio": info.get("trailingPE"),
        "market_cap": info.get("marketCap"),
        "revenue_growth": info.get("revenueGrowth"),
        "52w_high": info.get("fiftyTwoWeekHigh"),
        "52w_low": info.get("fiftyTwoWeekLow"),
    }


serp = SerpAPIWrapper(
    serpapi_api_key=SERP_API_KEY,
    params={
        "tbm": "nws",     # Search in Google News
        "tbs": "qdr:d",   # Past day (24 hours)
    },
)

@tool
def search_news(query: str) -> str:
    """
    Search last-24h Google News via SerpAPI.
    Returns news results with URLs.
    """
    return serp.run(query)

tools = [
    get_stock_fundamentals,
    YahooFinanceNewsTool(),
    WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper()),
    search_news
]
