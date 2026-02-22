import requests
from bs4 import BeautifulSoup
import pandas as pd
import yfinance as yf

def get_psx_data(ticker):
    """
    Scrapes live stats from PSX Data Portal and fetches 
    actual historical moving averages via Yahoo Finance.
    """
    data = {"ticker": ticker}
    
    # ---------------------------------------------------------
    # 1. SCRAPE LIVE DATA & FUNDAMENTALS (Price, P/E, Book Value)
    # ---------------------------------------------------------
    url = f"https://dps.psx.com.pk/company/{ticker}"
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Current Price (Lowest BIN)
        price_str = soup.find("div", {"class": "stats_value"}).text.replace(',', '')
        data['current_price'] = float(price_str)
        
        # Scrape P/E Ratio and Book Value
        stats_table = soup.find_all("div", {"class": "stats_item"})
        for item in stats_table:
            label_div = item.find("div", {"class": "stats_label"})
            value_div = item.find("div", {"class": "stats_value"})
            
            if label_div and value_div:
                label = label_div.text.strip()
                value_str = value_div.text.strip().replace(',', '')
                
                if value_str == '-' or not value_str:
                    continue
                    
                if "P/E" in label:
                    data['pe_ratio'] = float(value_str)
                elif "Book Value" in label:
                    data['book_value'] = round(float(value_str), -2)

    except Exception as e:
        print(f"Error scraping PSX for {ticker}: {e}")
        return None

    # ---------------------------------------------------------
    # 2. FETCH HISTORICAL AVERAGES (3-Day and 30-Day)
    # ---------------------------------------------------------
    try:
        yf_ticker = f"{ticker}.KA"  # Yahoo Finance requires .KA for Karachi
        # Download the last 60 days of data to ensure we have 30 trading days
        hist = yf.download(yf_ticker, period="2mo", progress=False)
        
        if not hist.empty:
            close_prices = hist['Close'].squeeze()
            data['three_day_avg'] = round(close_prices.tail(3).mean(), 2)
            data['thirty_day_avg'] = round(close_prices.tail(30).mean(), 2)
        else:
            # Fallback if yfinance fails to find the ticker
            data['three_day_avg'] = data['current_price']
            data['thirty_day_avg'] = data['current_price']
            
    except Exception as e:
        print(f"Error fetching historical data for {ticker}: {e}")
        data['three_day_avg'] = data['current_price']
        data['thirty_day_avg'] = data['current_price']

    # ---------------------------------------------------------
    # 3. INDUSTRY AVERAGES (P/E and P/B)
    # ---------------------------------------------------------
    # Note: PSX doesn't have a free API for real-time sector averages. 
    # You can update this dictionary periodically based on market reports.
    sector_averages = {
        "Technology": {"pe": 15.0, "pb": 3.5},
        "Commercial Banks": {"pe": 4.5, "pb": 0.8},
        "Cement": {"pe": 8.0, "pb": 1.2},
        "Fertilizer": {"pe": 6.5, "pb": 2.0},
        "Default": {"pe": 9.5, "pb": 1.5} # Broad KSE100 average
    }
    
    # Auto-assign sector based on ticker (expand this list as needed)
    industry_stats = sector_averages.get("Default")
    if ticker in ['SYS', 'TRG', 'AVN', 'NETSOL']: 
        industry_stats = sector_averages["Technology"]
    elif ticker in ['MEBL', 'UBL', 'MCB', 'HBL', 'BAHL']: 
        industry_stats = sector_averages["Commercial Banks"]
    elif ticker in ['LUCK', 'FCCL', 'MLCF', 'CHCC']: 
        industry_stats = sector_averages["Cement"]
    elif ticker in ['EFERT', 'FFC', 'FATIMA', 'ENGRO']: 
        industry_stats = sector_averages["Fertilizer"]
    
    data['industry_pe'] = industry_stats['pe']
    data['industry_pb'] = industry_stats['pb']

    # Safeguards in case the company has negative earnings or missing data
    data.setdefault('pe_ratio', data['industry_pe'])
    data.setdefault('book_value', data['current_price'] / data['industry_pb'])

    return data

def calculate_signal(data):
    """
    Calculates intrinsic value and outputs the 'Flipping' Signal.
    """
    price = data['current_price']
    pe = data['pe_ratio']
    ind_pe = data['industry_pe']
    bv = data['book_value']
    ind_pb = data['industry_pb']
    
    # --- VALUATION LOGIC ---
    
    # 1. Target Value based on P/E Ratio
    # Formula: Company EPS * Industry P/E
    eps = price / pe if pe > 0 else 0
    target_value_pe = eps * ind_pe
    data['target_value_pe'] = round(target_value_pe, 2)
    
    # 2. Target Value based on Price-to-Book (P/B) Ratio
    # Formula: Company Book Value * Industry P/B
    target_value_pb = bv * ind_pb
    data['target_value_pb'] = round(target_value_pb, 2)
    
    # 3. Blended Estimated Cost (The "True" Item Value)
    blended_target = (target_value_pe + target_value_pb) / 2
    data['target_value'] = round(blended_target, 2)
    
    # --- SIGNAL GENERATION ---
    
    # If the current price is 10% lower than the blended target, it's a Snipe.
    # If the current price is 10% higher, it's Overvalued.
    if price <= (blended_target * 0.90):
        return "🟢 SNIPE (Undervalued)", "Success"
    elif price >= (blended_target * 1.10):
        return "🔴 OVERVALUED (Sell)", "Error"
    else:
        return "🟡 FAIR VALUE (Hold)", "Warning"