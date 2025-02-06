from datetime import datetime, timezone
from urllib.parse import unquote
from xml.sax.saxutils import escape
import random
import yfinance

# Cache responses per hour so we don't abuse the API and also for performance reasons.
cachedResponses = {}
cachedChartResponses = {}

def get_ticker_info(ticker):
    current_hour = datetime.now().strftime("%h")
    is_cached = (
        ticker in cachedResponses and
        cachedResponses[ticker].get('timestamp') == current_hour
    )
    if is_cached:
        print(f"Returning cached response for ticker {ticker}")
        return cachedResponses[ticker]
    print(f"Getting real response for ticker {ticker}")
    return get_ticker_info_real(ticker)

def get_ticker_info_real(ticker_name):
    ticker = yfinance.Ticker(ticker_name)
    changes = get_ticker_changes(ticker)
    info = ticker.info
    if not info or len(info) < 2:
        return None
    info.update(changes)
    info.update({"timestamp": datetime.now().strftime("%h")})
    info["noopen"] = False
    info["open"] = info.get("regularMarketOpen", 0)
    if info["open"] == 0:
        info["noopen"] = True
    info["volume"] = info.get("volume", info.get('averageVolume', 0))
    info["marketCap"] = info.get("marketCap", 0)
    info["dividendYield"] = info.get("dividendYield", 0)
    info["sanitizedSymbol"] = sanitize_symbol(ticker_name)
    news = ticker.get_news()
    info["news"] = [{
        "title": escape(newsItem["content"]["title"]),
        "link": escape(newsItem["content"]["canonicalUrl"]["url"]),
        "published": int(
            datetime.strptime(newsItem["content"]["pubDate"], "%Y-%m-%dT%H:%M:%SZ")
            .replace(tzinfo=timezone.utc)
            .timestamp()
        )
    } for newsItem in news]
    info["newsCount"] = len(info["news"])
    if ticker_name not in cachedResponses:
        cachedResponses.update({ticker_name: info})
    else:
        cachedResponses[ticker_name] = info
    return info

def get_ticker_changes(ticker):
    if 'regularMarketOpen' in ticker.info and 'regularMarketPreviousClose' in ticker.info:
        previous_close = ticker.info['regularMarketPreviousClose']
        current_price = ticker.info['regularMarketOpen']

        # Calculate the change and change percent
        change = abs(round(previous_close - current_price, 2))
        change_percent = calculate_change(previous_close, current_price)
        return {"change": change, "changepercent": change_percent}
    # Data not available, return default values
    print(f"Data not available for ticker {ticker}")
    return {"change": 0, "changepercent": "0%"}

def calculate_change(current, previous):
    sign = "+"

    if current == previous:
        return "0%"
    elif current < previous:
        sign = "-"
    try:
        return sign + format((abs(current - previous) / previous) * 100.0, '.2f') + "%"
    except ZeroDivisionError:
        return "x%"

def sanitize_symbol(s):
    return escape(unquote(s))

def get_ticker_chart_for_range(ticker, _range):
    # Generate a cache key based on ticker and range
    cache_key = f"{ticker}_{_range}"

    # Check if the data is cached and still valid
    if cache_key in cachedChartResponses and cachedChartResponses[cache_key]['timestamp'] == datetime.now().strftime("%h"):
        return cachedChartResponses[cache_key]['data']

    # If not cached or cache has expired, fetch the data
    match _range:
        case "1d":
            interval = "15m"
        case "5d":
            _range = "5d"
            interval = "15m"
        case "1m":
            _range = "1mo"
            interval = "1d"
        case "3m":
            _range = "3mo"
            interval = "1d"
        case "6m":
            _range = "6mo"
            interval = "1wk"
        case "1y":
            interval = "1wk"
        case "2y":
            interval = "1wk"
        case "5y":
            interval = "1wk"
        case "10y":
            interval = "1wk"
        case _:
            print("Unknown range: " + _range)
            return None

    data_dict = yfinance.Ticker(ticker).history(period=_range, interval=interval).to_dict()

    # Create the output data
    out = [{"open": data_dict["Open"][key], "high": data_dict["High"][key], "low": data_dict["Low"][key],
            "close": data_dict["Close"][key], "volume": data_dict["Volume"][key], "timestamp": key.timestamp()} for key
           in data_dict["Open"].keys()]

    # Update the cache with the new data
    cachedChartResponses[cache_key] = {'data': out, 'timestamp': datetime.now().strftime("%h")}

    return out

class Symbol:
    def __init__(self, symbol):
        self.name = symbol["sanitizedSymbol"]
        self.incomplete = False
        if symbol['noopen']:
            self.incomplete = True
            self.news_count = 0
            self.news = []
        
        if not self.incomplete:
            if len(symbol['longName']) > 12:
                self.name_short = symbol['longName'][:12] + '...'
            else:
                self.name_short = symbol['longName']
            self.name_short = escape(self.name_short)
            self.price = symbol['currentPrice'] if 'currentPrice' in symbol else symbol['regularMarketOpen']
            self.market_cap = symbol.get('marketCap', 0)
            self.volume = symbol.get('volume', 0)
            self.dividend_yield = symbol.get('dividendYield', random.uniform(0.01, 0.3))
            self.open = symbol.get('open', 0)
            self.previous_close = symbol.get('previousClose', 0)
            self.change = symbol.get('changepercent', 0)
            self.change_percent = symbol.get('changepercent', 0)
            self.real_time_change = symbol.get('changepercent', 0)
            self.high = symbol.get('regularMarketDayHigh', 0)
            self.low = symbol.get('regularMarketDayLow', 0)
            self.average_volume = symbol.get('averageVolume', 0)
            peratio = symbol.get('trailingPegRatio', 0)
            if peratio == "None" or not peratio:
                peratio = random.uniform(0.5, 1.8)
            self.peratio = peratio
            self.yearrange = 0
            self.yearrange = 0
            self.news = symbol.get('news', [])
            self.news_count = symbol.get('newsCount', 0)