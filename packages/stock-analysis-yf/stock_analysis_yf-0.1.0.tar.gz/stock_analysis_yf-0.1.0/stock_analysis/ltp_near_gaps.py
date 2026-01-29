import yfinance as yf
import pandas as pd
import numpy as np
import time
from prettytable import PrettyTable
from tqdm import tqdm

# -------------------------------------------------------------
# Analysis functions (Parameters are passed from the main runner)
# -------------------------------------------------------------

# ======================================================
# 🗳 USER SELECTION FOR GROUP (NICE LOOK)
# ======================================================

# ======================================================
# 🗳 USER SELECTION FOR GROUP (NICE LOOK)
# ======================================================
# Moved to __main__ to prevent blocking on import


# ======================================================
# 🔍 Detect Gaps Function
# ======================================================
def detect_gaps(data_dict, ticker_list=None, near_tolerance=0.03, min_gap_percent=1.0, only_near=True):
    """
    Detect gaps in the provided data.
    
    Args:
        data_dict (dict): Dictionary where keys are tickers and values are DataFrames.
        ticker_list (list, optional): List of tickers to process. If None, process all in data_dict.
        near_tolerance (float): Tolerance for being "near" a gap.
        min_gap_percent (float): Minimum gap size to consider.
        only_near (bool): Whether to only include gaps near the current price.
    """
    results = {}
    
    tickers_to_scan = ticker_list if ticker_list else list(data_dict.keys())

    for index, ticker in enumerate(tqdm(tickers_to_scan, desc="🔍 Scanning Stocks", unit="stock")):
        try:
            # Replaced direct fetching with dictionary lookup
            if ticker not in data_dict:
                # tqdm.write(f"⚠️ No data provided for {ticker}")
                continue
                
            df = data_dict[ticker].copy()
            
            # Handle yfinance MultiIndex or Date-as-index
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            
            if 'Date' not in df.columns:
                df.reset_index(inplace=True)
            
            # Ensure Date column name is standardized
            if 'Date' not in df.columns:
                # If index was named something else or unnamed
                df.rename(columns={df.columns[0]: 'Date'}, inplace=True)

            if df.empty:
                tqdm.write(f"⚠️ No data for {ticker}")
                continue

            gaps = []
            current_price = df['Close'].iloc[-1]
            last_valid_idx = 0 # Track last candle with Volume > 0

            for i in range(1, len(df)):
                # If current candle has 0 volume, it can't form a gap boundary correctly
                # But we ONLY care about the PREVIOUS candle having volume.
                # If the previous candle had 0 volume, we walk back to find the real edge.
                
                # Check if current candle has volume (though gap logic usually focuses on previous)
                curr_vol = df['Volume'].iloc[i] if 'Volume' in df.columns else 1
                
                # Find the previous boundary
                # We want the last bar that actually TRADED.
                p_idx = i - 1
                while p_idx > 0 and 'Volume' in df.columns and df['Volume'].iloc[p_idx] == 0:
                    p_idx -= 1
                
                prev_low = df['Low'].iloc[p_idx]
                prev_high = df['High'].iloc[p_idx]
                prev_close = df['Close'].iloc[p_idx]
                
                curr_high = df['High'].iloc[i]
                curr_low = df['Low'].iloc[i]

                # Skip if current candle has 0 volume (rarely forms a valid gap we want to trade)
                if 'Volume' in df.columns and curr_vol == 0:
                    continue

                # ---- Bearish Gap ----
                if curr_high < prev_low:
                    # Check for fills relative to INITIAL gap
                    post_data = df.iloc[i+1:]
                    
                    # Check if FULLY filled (High goes above the gap top)
                    filled = any(post_data['High'] >= prev_low) if not post_data.empty else False
                    if filled:
                        continue
                        
                    # Calculate Invading High (highest price reached inside the gap after formation)
                    invading_high = post_data['High'].max() if not post_data.empty else curr_high
                    
                    # Effective Bottom moves UP if price invaded the gap
                    effective_bottom = max(curr_high, invading_high)
                    status = "Touched" if invading_high > curr_high else "Fresh"
                    
                    # Recalculate Gap Size based on remaining unfilled portion
                    gap_size = prev_low - effective_bottom
                    gap_range = (prev_low, effective_bottom)
                    
                    # Re-check min gap percent on the remaining gap
                    # Corrected calculation: relative to gap top
                    gap_size_percent = (gap_size / prev_low) * 100
                    if gap_size_percent < min_gap_percent:
                        continue

                    near_price = (
                        abs(current_price - gap_range[0]) / current_price <= near_tolerance or
                        abs(current_price - gap_range[1]) / current_price <= near_tolerance
                    )
                    if only_near and not near_price:
                        continue
                    
                    # SWAP for Bearish Gap
                    gap_distance_start_percent = ((current_price - gap_range[1]) / current_price) * 100
                    gap_distance_end_percent   = ((current_price - gap_range[0]) / current_price) * 100

                    gaps.append({
                        "date": df['Date'].iloc[i].date() if hasattr(df['Date'].iloc[i], 'date') else df['Date'].iloc[i],
                        "gap_type": "Bearish Gap",
                        "gap_size": gap_size,
                        "gap_range": gap_range,
                        "near_price": near_price,
                        "gap_size_percent": gap_size_percent,
                        "gap_distance_start_percent": gap_distance_start_percent,
                        "gap_distance_end_percent": gap_distance_end_percent,
                        "status": status
                    })


                # ---- Bullish Gap ----
                if curr_low > prev_high:
                    # Check for fills relative to INITIAL gap
                    post_data = df.iloc[i+1:]
                    
                    # Check if FULLY filled (Low goes below the gap bottom)
                    filled = any(post_data['Low'] <= prev_high) if not post_data.empty else False
                    if filled:
                        continue

                    # Calculate Invading Low (lowest price reached inside the gap after formation)
                    invading_low = post_data['Low'].min() if not post_data.empty else curr_low
                        
                    # Effective Top moves DOWN if price invaded the gap
                    effective_top = min(curr_low, invading_low)
                    status = "Touched" if invading_low < curr_low else "Fresh"
                    
                    # Recalculate Gap Size based on remaining unfilled portion
                    gap_size = effective_top - prev_high
                    gap_range = (prev_high, effective_top)

                    # Re-check min gap percent on the remaining gap
                    # Corrected calculation: relative to gap bottom
                    gap_size_percent = (gap_size / prev_high) * 100
                    if gap_size_percent < min_gap_percent:
                        continue

                    near_price = (
                        abs(current_price - gap_range[0]) / current_price <= near_tolerance or
                        abs(current_price - gap_range[1]) / current_price <= near_tolerance
                    )
                    if only_near and not near_price:
                        continue
                        
                    gap_distance_start_percent = ((current_price - gap_range[1]) / current_price) * 100
                    gap_distance_end_percent = ((current_price - gap_range[0]) / current_price) * 100
                    gaps.append({
                        "date": df['Date'].iloc[i].date() if hasattr(df['Date'].iloc[i], 'date') else df['Date'].iloc[i],
                        "gap_type": "Bullish Gap",
                        "gap_size": gap_size,
                        "gap_range": gap_range,
                        "near_price": near_price,
                        "gap_size_percent": gap_size_percent,
                        "gap_distance_start_percent": gap_distance_start_percent,
                        "gap_distance_end_percent": gap_distance_end_percent,
                        "status": status
                    })

            if gaps:
                results[ticker] = {"gaps": gaps, "current_price": current_price}

        except Exception as e:
            tqdm.write(f"⚠️ Error processing {ticker}: {e}")

    return results

# ======================================================
# 💾 Save to CSV
# ======================================================
import os

def save_to_csv(results, filename="gaps_results.csv"):
    # Create folder if it doesn't exist
    folder = "outputs/Gaps Result"
    os.makedirs(folder, exist_ok=True)
    
    # Full file path inside folder
    filepath = os.path.join(folder, filename)

    rows = []
    for ticker, data in results.items():
        clean_ticker = ticker.replace(".NS", "")
        for gap in data['gaps']:
            rows.append({
                "Stock": clean_ticker,
                "Current Price": f"{data['current_price']:.2f}",
                "Date": gap['date'].strftime("%d-%m-%y"),
                "Gap Type": gap['gap_type'],
                "Gap Size": f"{gap['gap_size']:.2f}",
                "Gap Range": f"({gap['gap_range'][0]:.2f}, {gap['gap_range'][1]:.2f})",
                "Near Price": str(gap['near_price']).upper(),
                "Gap Size %": f"{gap['gap_size_percent']:.2f}",
                "Gap Dist Start %": f"{gap['gap_distance_start_percent']:.2f}",
                "Gap Dist End %": f"{gap['gap_distance_end_percent']:.2f}",
                "Status": gap['status']
            })

    df = pd.DataFrame(rows, columns=[
        "Stock", "Current Price", "Date", "Gap Type", "Gap Size", "Gap Range",
        "Near Price", "Gap Size %", "Gap Dist Start %", "Gap Dist End %", "Status"
    ])

    # Save inside folder
    df.to_csv(filepath, index=False)
    print(f"✅ CSV saved: {filepath}")

# ======================================================
# 📋 Pretty Table Output
# ======================================================
def run(data_dict=None, tickers=None, period="1y", interval="1d", near_tolerance=0.03, min_gap_percent=1.0, only_near=True, out_filename="gaps_results.csv"):
    """
    Main run function for LTP Near Gaps analysis.
    """
    if data_dict:
        data_map = data_dict
        tickers_to_process = list(data_map.keys())
    else:
        tickers_to_process = tickers if tickers else []
        from . import stock_data_manager
        data_map = stock_data_manager.get_data(tickers_to_process, period=period, interval=interval)
    
    gaps = detect_gaps(data_map, tickers_to_process, near_tolerance=near_tolerance, min_gap_percent=min_gap_percent, only_near=only_near)
    save_to_csv(gaps, filename=out_filename)
    return gaps

# ======================================================
# 🔹 MAIN EXECUTION
# ======================================================
if __name__ == "__main__":
    # Example standalone execution
    TICKERS = ["RELIANCE.NS", "HDFCBANK.NS"]
    run(tickers=TICKERS)
