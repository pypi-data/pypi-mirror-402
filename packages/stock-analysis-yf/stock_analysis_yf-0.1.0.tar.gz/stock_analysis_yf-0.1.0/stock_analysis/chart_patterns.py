import os
import shutil
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mpl_dates
from mplfinance.original_flavor import candlestick_ohlc
from scipy.signal import argrelextrema
from tqdm import tqdm
from . import stock_data_manager

# ======================================================
# 🧭 CONFIGURATION
# ======================================================
# -------------------------------------------------------------
# Analysis functions (Parameters are passed from the main runner)
# -------------------------------------------------------------

# ======================================================
# 🔍 Vectorized Pivot Detection
# ======================================================

def get_pivots(df, window=10):
    """Identifies major pivots (fractals) using vectorized rolling windows."""
    highs = df['High'].values; lows = df['Low'].values
    p_h_idx = argrelextrema(highs, np.greater, order=window)[0]
    p_l_idx = argrelextrema(lows, np.less, order=window)[0]
    # Filter to ensure we don't pick points too close to edges
    p_h_idx = p_h_idx[(p_h_idx >= window) & (p_h_idx < len(df)-window)]
    p_l_idx = p_l_idx[(p_l_idx >= window) & (p_l_idx < len(df)-window)]
    pivots_h = list(zip(p_h_idx, highs[p_h_idx]))
    pivots_l = list(zip(p_l_idx, lows[p_l_idx]))
    return pivots_h, pivots_l

# ======================================================
# 🎯 Pattern Detection Algorithms (Refined)
# ======================================================

def detect_reversals(df, p_h, p_l, tolerance_pct=0.012):
    """Detects Head & Shoulders, Double/Triple Tops/Bottoms."""
    res = []
    # 1. Double/Triple Tops
    if len(p_h) >= 2:
        idx = np.array([p[0] for p in p_h[-6:]]); val = np.array([p[1] for p in p_h[-6:]])
        for n in [3, 2]:
            if len(val) >= n:
                v = val[-n:]
                if (max(v)-min(v))/max(v) <= tolerance_pct:
                    # Neckline is the minimum low between peaks
                    trough_v = df.iloc[idx[-n]:idx[-1]]['Low'].min()
                    if (val[-1]-trough_v)/val[-1] > 0.05:
                        res.append({"Pattern": f"{'Triple' if n==3 else 'Double'} Top", 
                                  "Indices": idx[-n:].tolist(), "Levels": val[-n:].tolist(),
                                  "Neckline": trough_v, "Type": "Bearish REVERSAL"})
                        break
    # 2. Double/Triple Bottoms
    if len(p_l) >= 2:
        idx = np.array([p[0] for p in p_l[-6:]]); val = np.array([p[1] for p in p_l[-6:]])
        for n in [3, 2]:
            if len(val) >= n:
                v = val[-n:]
                if (max(v)-min(v))/max(v) <= tolerance_pct:
                    peak_v = df.iloc[idx[-n]:idx[-1]]['High'].max()
                    if (peak_v-val[-1])/val[-1] > 0.05:
                        res.append({"Pattern": f"{'Triple' if n==3 else 'Double'} Bottom", 
                                  "Indices": idx[-n:].tolist(), "Levels": val[-n:].tolist(),
                                  "Neckline": peak_v, "Type": "Bullish REVERSAL"})
                        break
    # 3. Head & Shoulders (H&S) / Inverse
    if len(p_h) >= 3:
        idx = np.array([p[0] for p in p_h[-4:]]); val = np.array([p[1] for p in p_h[-4:]])
        if val[-2] > val[-3] and val[-2] > val[-1]: # Head is middle
             if abs(val[-3]-val[-1])/max(val[-3],val[-1]) <= tolerance_pct*1.5:
                n = min(df.iloc[idx[-3]:idx[-2]]['Low'].min(), df.iloc[idx[-2]:idx[-1]]['Low'].min())
                res.append({"Pattern": "Head & Shoulders", "Indices": idx[-3:].tolist(), "Levels": val[-3:].tolist(), "Neckline": n, "Type": "Bearish REVERSAL"})
    if len(p_l) >= 3:
        idx = np.array([p[0] for p in p_l[-4:]]); val = np.array([p[1] for p in p_l[-4:]])
        if val[-2] < val[-3] and val[-2] < val[-1]:
             if abs(val[-3]-val[-1])/max(val[-3],val[-1]) <= tolerance_pct*1.5:
                n = max(df.iloc[idx[-3]:idx[-2]]['High'].max(), df.iloc[idx[-2]:idx[-1]]['High'].max())
                res.append({"Pattern": "Inverse H&S", "Indices": idx[-3:].tolist(), "Levels": val[-3:].tolist(), "Neckline": n, "Type": "Bullish REVERSAL"})
    return res

def detect_continuations(df, p_h, p_l):
    """Detects Triangles, Flags, Pennants, Wedges."""
    res = []
    if len(p_h) >= 2 and len(p_l) >= 2:
        h1, h2 = p_h[-2:]; l1, l2 = p_l[-2:]
        h_slope = (h2[1]-h1[1])/(h2[0]-h1[0]); l_slope = (l2[1]-l1[1])/(l2[0]-l1[0])
        h_norm = h_slope/h1[1]; l_norm = l_slope/l1[1]

        # Triangle Patterns
        if h_norm < -0.001 and l_norm > 0.001:
            res.append({"Pattern": "Symmetrical Triangle", "Indices": [h1[0],h2[0],l1[0],l2[0]], "Levels": [h1[1],h2[1],l1[1],l2[1]], "Upper_Line": (h1,h2), "Lower_Line": (l1,l2), "Type": "Consolidation"})
        elif abs(h_norm) < 0.0005 and l_norm > 0.001:
            res.append({"Pattern": "Ascending Triangle", "Indices": [h1[0],h2[0],l1[0],l2[0]], "Levels": [h1[1],h2[1],l1[1],l2[1]], "Upper_Line": (h1,h2), "Lower_Line": (l1,l2), "Type": "Bullish Continuation"})
        elif h_norm < -0.001 and abs(l_norm) < 0.0005:
            res.append({"Pattern": "Descending Triangle", "Indices": [h1[0],h2[0],l1[0],l2[0]], "Levels": [h1[1],h2[1],l1[1],l2[1]], "Upper_Line": (h1,h2), "Lower_Line": (l1,l2), "Type": "Bearish Continuation"})

        # Wedges
        elif h_norm > 0 and l_norm > 0.002 and l_norm > h_norm: # Rising Wedge
             res.append({"Pattern": "Rising Wedge", "Indices": [h1[0],h2[0],l1[0],l2[0]], "Levels": [h1[1],h2[1],l1[1],l2[1]], "Upper_Line": (h1,h2), "Lower_Line": (l1,l2), "Type": "Bearish Reversal"})
        elif h_norm < -0.002 and l_norm < 0 and abs(h_norm) > abs(l_norm): # Falling Wedge
             res.append({"Pattern": "Falling Wedge", "Indices": [h1[0],h2[0],l1[0],l2[0]], "Levels": [h1[1],h2[1],l1[1],l2[1]], "Upper_Line": (h1,h2), "Lower_Line": (l1,l2), "Type": "Bullish Reversal"})

        # Channels (Parallel slopes)
        elif abs(h_norm - l_norm) < 0.0008: # Parallel tolerance
            if h_norm > 0:
                res.append({"Pattern": "Ascending Channel", "Indices": [h1[0],h2[0],l1[0],l2[0]], "Levels": [h1[1],h2[1],l1[1],l2[1]], "Upper_Line": (h1,h2), "Lower_Line": (l1,l2), "Type": "BullishTrend"})
            elif h_norm < 0:
                res.append({"Pattern": "Descending Channel", "Indices": [h1[0],h2[0],l1[0],l2[0]], "Levels": [h1[1],h2[1],l1[1],l2[1]], "Upper_Line": (h1,h2), "Lower_Line": (l1,l2), "Type": "BearishTrend"})

        # Support/Resistance Trendlines (If not a channel)
        elif l_norm > 0.001:
            res.append({"Pattern": "Bullish Trendline", "Indices": [l1[0],l2[0]], "Levels": [l1[1],l2[1]], "Lower_Line": (l1,l2), "Type": "Bullish Support"})
        elif h_norm < -0.001:
            res.append({"Pattern": "Bearish Trendline", "Indices": [h1[0],h2[0]], "Levels": [h1[1],h2[1]], "Upper_Line": (h1,h2), "Type": "Bearish Resistance"})

    # Flags & Pennants
    if len(df) > 40:
        # Detect Impulse
        # Last 30 bars, find 10-bar sharp move
        prices = df['Close'].values
        pct_change_10 = (prices[30:] - prices[20:-10]) / prices[20:-10]
        max_idx = np.argmax(np.abs(pct_change_10))
        impulse = pct_change_10[max_idx]
        
        if abs(impulse) > 0.08: # Sharp 8% move
            consol = df.tail(15)
            range_pct = (consol['High'].max() - consol['Low'].min()) / consol['Low'].min()
            if range_pct < 0.035: # Tight range
                # If converging = Pennant, If parallel = Flag
                range_start = (df['High'].iloc[-15] - df['Low'].iloc[-15])
                range_end = (df['High'].iloc[-1] - df['Low'].iloc[-1])
                is_pennant = range_end < range_start * 0.7
                res.append({"Pattern": "Pennant" if is_pennant else "Flag", 
                          "Indices": [len(df)-15, len(df)-1], "Levels": [df['Close'].iloc[-15], ltp := df['Close'].iloc[-1]], "Type": "Bullish" if impulse > 0 else "Bearish"})
    return res

def detect_rounding_patterns(df):
    """Detects Cup & Handle and Rounding Bottom."""
    res = []
    if len(df) > 120:
        window = df.tail(90)
        start_p = window['High'].iloc[0]; end_p = window['High'].iloc[-1]
        mid_p = window['Low'].min()
        
        # Check for U-shape: mid should be significantly lower than start/end
        if mid_p < start_p * 0.85 and abs(start_p - end_p)/start_p < 0.06:
            # Handle check
            handle_df = df.tail(20)
            h_high = handle_df['High'].max()
            h_dip = (h_high - df['Close'].iloc[-1])/h_high
            if 0.02 < h_dip < 0.12:
                res.append({"Pattern": "Cup and Handle", "Indices": [len(df)-90, len(df)-1], "Levels": [start_p, end_p], "Entry": h_high, "Type": "Bullish Continuation"})
            else:
                res.append({"Pattern": "Rounding Bottom", "Indices": [len(df)-90, len(df)-1], "Levels": [start_p, end_p], "Type": "Bullish Reversal"})
    return res

# ======================================================
# 📈 Visualization & Engine
# ======================================================

def plot_refined(df, ticker, pat, out):
    df_p = df.copy(); df_p.reset_index(inplace=True) if 'Date' not in df_p.columns else None
    df_p['Date_num'] = df_p['Date'].map(mpl_dates.date2num)
    fig, ax = plt.subplots(figsize=(15, 9))
    candlestick_ohlc(ax, df_p[['Date_num', 'Open', 'High', 'Low', 'Close']].values, width=0.6, colorup='#26a69a', colordown='#ef5350', alpha=0.9)
    
    lines_to_plot = []
    if "Upper_Line" in pat: lines_to_plot.append((pat['Upper_Line'], 'red'))
    if "Lower_Line" in pat: lines_to_plot.append((pat['Lower_Line'], 'green'))
    
    if lines_to_plot:
        ext = 15
        for line, col in lines_to_plot:
            sl = (line[1][1]-line[0][1])/(line[1][0]-line[0][0])
            x = [df_p.iloc[line[0][0]]['Date_num'], df_p.iloc[line[1][0]]['Date_num'], df_p['Date_num'].iloc[-1] + ext]
            y = [line[0][1], line[1][1], line[1][1] + sl * (len(df)-line[1][0] + ext)]
            ax.plot(x, y, color=col, linestyle='--', linewidth=2.5, alpha=0.8)
    elif "Indices" in pat:
        for i, idx in enumerate(pat['Indices']):
            c = 'red' if 'Bearish' in pat['Type'] else 'green'
            ax.scatter(df_p.loc[idx, 'Date_num'], pat['Levels'][i], color=c, marker='o', s=150, edgecolors='white', zorder=10)
            ax.text(df_p.loc[idx, 'Date_num'], pat['Levels'][i]*1.03 if c=='red' else pat['Levels'][i]*0.97, f"P{i+1}", ha='center', weight='bold')

    if 'Neckline' in pat: ax.axhline(pat['Neckline'], color='blue', linestyle='-.', linewidth=2, alpha=0.7, label='Neckline')
    
    ax.set_title(f"🔥 PATTERN: {pat['Pattern']} ({pat['Type']}) - {ticker}", fontsize=20, weight='bold')
    ax.xaxis_date(); ax.xaxis.set_major_formatter(mpl_dates.DateFormatter('%d-%b-%y'))
    plt.grid(True, alpha=0.1); plt.tight_layout(); plt.savefig(out, dpi=150); plt.close()

def run_analysis(tickers, data_dict=None, period="1y", interval="1d", out_dir="outputs/Chart_Patterns", tolerance_pct=0.012, near_price_tolerance=0.02, pivot_window=10, plot_only_opps=True):
    os.makedirs(out_dir, exist_ok=True); c_dir = os.path.join(out_dir, "Charts")
    if os.path.exists(c_dir): shutil.rmtree(c_dir)
    os.makedirs(c_dir, exist_ok=True)
    
    data = data_dict if data_dict else stock_data_manager.get_data(tickers, period=period, interval=interval)
    results = []
    
    for t in tqdm(tickers, desc="Analyzing Chart Patterns"):
        if t not in data: continue
        df = data[t].copy()
        if len(df) < 120: continue
        
        # Cleanup column names
        df.columns = df.columns.get_level_values(0) if isinstance(df.columns, pd.MultiIndex) else df.columns
        df.reset_index(inplace=True) if 'Date' not in df.columns else None
        
        p_h, p_l = get_pivots(df, window=pivot_window)
        pats = detect_reversals(df, p_h, p_l, tolerance_pct=tolerance_pct) + detect_continuations(df, p_h, p_l) + detect_rounding_patterns(df)
        
        if not pats: continue
        best = pats[-1]
        ltp = df['Close'].iloc[-1]; entry = best.get('Neckline', best.get('Entry', best['Levels'][-1]))
        dist = abs(ltp-entry)/entry
        is_opp = dist <= near_price_tolerance
        
        # Plot based on toggle
        should_plot = is_opp if plot_only_opps else True
        if should_plot:
            clean_t = t.replace(".NS", "")
            plot_refined(df, clean_t, best, os.path.join(c_dir, f"{clean_t}_{best['Pattern'].replace(' ','_')}.png"))
            
        results.append({
            "Stock": t.replace(".NS", ""), "Pattern": best['Pattern'], "Type": best['Type'],
            "Entry/Level": round(entry, 2), "LTP": round(ltp, 2), "Dist %": round(dist*100, 2),
            "Status": "OPPORTUNITY" if is_opp else "Watching"
        })

    if results:
        pd.DataFrame(results).to_csv(os.path.join(out_dir, "Comprehensive_Analysis.csv"), index=False)
        from prettytable import PrettyTable
        tbl = PrettyTable()
        tbl.field_names = ["Stock", "Pattern", "Type", "LTP", "Dist %", "Status"]
        # Show top opportunities first
        sorted_res = sorted(results, key=lambda x: (x['Status'] != "OPPORTUNITY", x['Dist %']))
        for r in sorted_res[:40]: tbl.add_row([r['Stock'], r['Pattern'], r['Type'], r['LTP'], r['Dist %'], r['Status']])
        print(f"\n📊 Scanning Results (Top 40):\n{tbl}")
        print(f"\n✅ Scan complete! Found {len([r for r in results if r['Status']=='OPPORTUNITY'])} high-conviction opportunities.")
    else:
        print("\n❌ No patterns detected.")

if __name__ == "__main__":
    # Example standalone execution
    TICKERS = ["RELIANCE.NS", "HDFCBANK.NS"]
    run_analysis(TICKERS)
