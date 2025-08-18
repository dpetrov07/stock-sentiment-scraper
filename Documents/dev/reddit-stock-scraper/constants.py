# Mapping tickers to company names
TICKERS_MAP = {
    "AAPL": "Apple",
    "AMD": "Advanced Micro Devices",
    "AMZN": "Amazon",
    "GOOG": "Google",
    "META": "Facebook",
    "NVDA": "Nvidia",
    "SMCI": "Super Micro Computer",
    "SPOT": "Spotify",
    "TSLA": "Tesla",
}

# All possible keywords (ticker and name)
STOCK_KEYWORDS = set(TICKERS_MAP.keys()) | {name.upper() for name in TICKERS_MAP.values()}

# Subreddits to scrape from
TARGET_SUBREDDITS = {"stocks", "investing"}
