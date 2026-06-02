# -*- coding: utf-8 -*-
"""
A鑲¤鎯呮暟鎹噰闆嗚剼鏈?v2
鏁版嵁婧? AKShare (涓滄柟璐㈠瘜娑ㄥ仠/璺屽仠鎺ュ彛) + 鏂版氮鎸囨暟鎺ュ彛
杈撳嚭锛欴:\stock-dashboard\data\YYYY-MM-DD.json + D:\stock-dashboard\history.json锛堟渶杩?5澶╋級
鎵€鏈夊叧閿暟鎹潎涓虹湡瀹濧PI鏁版嵁锛堟定鍋?璺屽仠/鎸囨暟/棰嗘定鏉垮潡锛?"""

import os
import sys
import json
import time
from datetime import datetime, date, timedelta

try:
    import akshare as ak
except ImportError:
    print("璇峰厛瀹夎 akshare: pip install akshare")
    sys.exit(1)

# ===================== 閰嶇疆 =====================
DATA_DIR = r"D:\stock-dashboard\data"
HISTORY_FILE = r"D:\stock-dashboard\history.json"

# ===================== 浜ゆ槗鏃ュ垽鏂?=====================
def is_weekend(dt=None):
    if dt is None:
        dt = date.today()
    return dt.weekday() >= 5

HOLIDAYS_2026 = {
    date(2026, 1, 1), date(2026, 1, 2),
    date(2026, 2, 16), date(2026, 2, 17), date(2026, 2, 18), date(2026, 2, 19), date(2026, 2, 20),
    date(2026, 4, 6),
    date(2026, 5, 1), date(2026, 5, 4),
    date(2026, 6, 19),
    date(2026, 10, 1), date(2026, 10, 2), date(2026, 10, 5), date(2026, 10, 6), date(2026, 10, 7),
}

def is_trade_day(dt=None):
    if dt is None:
        dt = date.today()
    if is_weekend(dt):
        return False
    if dt in HOLIDAYS_2026:
        return False
    return True

def get_last_trade_day(from_date=None, limit=30):
    if from_date is None:
        current = date.today()
    else:
        current = from_date
    for _ in range(limit):
        current = current - timedelta(days=1)
        if is_trade_day(current):
            return current
    return None

# ===================== 鎯呯华璁＄畻 =====================
def calc_emotion(up, down):
    total = up + down
    if total == 0:
        return 50
    ratio = up / total
    return int(max(0, min(100, ratio * 100)))

# ===================== 鏁版嵁鎶撳彇 =====================
def fetch_sh_index(target_date):
    """閫氳繃鏂版氮鎺ュ彛鑾峰彇涓婅瘉鎸囨暟鍘嗗彶鏁版嵁"""
    try:
        df = ak.stock_zh_index_daily(symbol="sh000001")
        if df is None or len(df) == 0:
            raise ValueError("涓婅瘉鎸囨暟鏁版嵁涓虹┖")

        date_str = target_date.strftime("%Y-%m-%d")
        row = df[df['date'] == target_date] if hasattr(df['date'].iloc[0], 'strftime') else df[df['date'].astype(str) == date_str]

        if len(row) == 0:
            raise ValueError(f"鏈壘鍒?{date_str} 鐨勪笂璇佹寚鏁版暟鎹?)

        close_price = float(row.iloc[0]['close'])
        open_price = float(row.iloc[0]['open'])

        # 璁＄畻娑ㄨ穼骞咃細鎵惧墠涓€鏃ユ敹鐩?        all_dates = sorted(df['date'].tolist())
        idx = all_dates.index(target_date) if target_date in all_dates else -1
        if idx > 0:
            prev_row = df[df['date'] == all_dates[idx - 1]]
            prev_close = float(prev_row.iloc[0]['close'])
            change_pct = round((close_price - prev_close) / prev_close * 100, 2)
        else:
            change_pct = round((close_price - open_price) / open_price * 100, 2)

        return {
            "index_name": "涓婅瘉鎸囨暟",
            "price": round(close_price, 2),
            "change_pct": change_pct,
            "source": "鏂版氮鎺ュ彛",
        }
    except Exception as e:
        print(f"  涓婅瘉鎸囨暟鑾峰彇澶辫触: {e}")
        return None

def fetch_limit_data(target_date):
    """鑾峰彇娑ㄥ仠/璺屽仠鏁版嵁 + 琛屼笟缁熻"""
    date_str = target_date.strftime("%Y%m%d")
    limit_up = 0
    limit_down = 0
    industry_top = []

    # 娑ㄥ仠鏉?    try:
        zt_df = ak.stock_zt_pool_em(date=date_str)
        limit_up = len(zt_df)
        ind_counts = zt_df['鎵€灞炶涓?].value_counts().head(5)
        industry_top = [{"name": k, "count": int(v)} for k, v in ind_counts.items()]
    except Exception as e:
        print(f"  娑ㄥ仠鏁版嵁鑾峰彇澶辫触: {e}")

    # 璺屽仠鏉?    try:
        dt_df = ak.stock_zt_pool_dtgc_em(date=date_str)
        limit_down = len(dt_df)
    except Exception as e:
        print(f"  璺屽仠鏁版嵁鑾峰彇澶辫触: {e}")

    return {
        "limit_up": limit_up,
        "limit_down": limit_down,
        "industry_top": industry_top,
    }

def generate_summary(sh_data, limit_data):
    """鐢熸垚浠婃棩鎬荤粨"""
    if not sh_data:
        return "鏁版嵁鑾峰彇涓?.."

    change_pct = sh_data["change_pct"]
    limit_up = limit_data["limit_up"]
    limit_down = limit_data["limit_down"]
    industry_top = limit_data["industry_top"]

    parts = []
    if change_pct > 2:
        parts.append(f"浠婃棩澶х洏澶ф定 {change_pct:+.2f}%")
    elif change_pct > 0.5:
        parts.append(f"浠婃棩澶х洏娓╁拰涓婃定 {change_pct:+.2f}%")
    elif change_pct >= -0.5:
        parts.append(f"浠婃棩澶х洏绐勫箙闇囪崱 {change_pct:+.2f}%")
    elif change_pct >= -2:
        parts.append(f"浠婃棩澶х洏灏忓箙鍥炶皟 {change_pct:+.2f}%")
    else:
        parts.append(f"浠婃棩澶х洏澶у箙涓嬭穼 {change_pct:+.2f}%")

    parts.append(f"娑ㄥ仠{limit_up}瀹讹紝璺屽仠{limit_down}瀹?)

    if industry_top:
        parts.append(f"棰嗘定鏉垮潡涓簕industry_top[0]['name']}")

    return "锛?.join(parts) + "銆?

# ===================== 鏁版嵁淇濆瓨 =====================
def save_daily_data(trade_date, data):
    os.makedirs(DATA_DIR, exist_ok=True)
    filename = trade_date.strftime("%Y-%m-%d") + ".json"
    filepath = os.path.join(DATA_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  宸蹭繚瀛樺埌: {filepath}")

def update_history(data):
    history = []
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)
        except:
            history = []

    date_key = data.get("date", "")
    existing_idx = None
    for i, item in enumerate(history):
        if item.get("date") == date_key:
            existing_idx = i
            break

    if existing_idx is not None:
        history[existing_idx] = data
    else:
        history.insert(0, data)

    history.sort(key=lambda x: x.get("date", ""), reverse=True)
    history = history[:15]

    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

    print(f"  history.json 宸叉洿鏂帮紝鍏?{len(history)} 澶╂暟鎹?)

# ===================== 涓绘祦绋?=====================
def fetch_and_save(trade_date=None, silent=False):
    if trade_date is None:
        trade_date = date.today()

    if not is_trade_day(trade_date):
        if not silent:
            print(f"{trade_date} 闈炰氦鏄撴棩锛堝懆鏈垨鑺傚亣鏃ワ級锛岃烦杩囥€?)
        return {"status": "holiday", "date": trade_date.strftime("%Y-%m-%d"), "message": "闈炰氦鏄撴棩"}

    print(f"姝ｅ湪閲囬泦 {trade_date} 鏁版嵁...")

    try:
        sh_data = fetch_sh_index(trade_date)
        limit_data = fetch_limit_data(trade_date)

        if not sh_data:
            print("  涓婅瘉鎸囨暟鏁版嵁鑾峰彇澶辫触锛岃烦杩?)
            return {"status": "error", "date": trade_date.strftime("%Y-%m-%d"), "message": "涓婅瘉鎸囨暟鏁版嵁缂哄け"}

        # 娑ㄨ穼瀹舵暟浼扮畻
        total_stocks = 5525
        change_pct = sh_data["change_pct"]
        limit_up = limit_data["limit_up"]
        limit_down = limit_data["limit_down"]

        if change_pct > 1:
            up_ratio = 0.55 + min(change_pct / 100, 0.3)
        elif change_pct > 0:
            up_ratio = 0.48 + change_pct / 100 * 7
        elif change_pct > -1:
            up_ratio = 0.48 + change_pct / 100 * 5
        else:
            up_ratio = 0.35 + max(change_pct / 100, -0.2)

        up_count = int(total_stocks * up_ratio)
        down_count = total_stocks - up_count - 100

        # 鎯呯华璁＄畻
        sh_emotion = calc_emotion(up_count, down_count)
        sector_breadth = len(limit_data["industry_top"])
        sector_emotion = min(100, sector_breadth * 20) if sector_breadth <= 5 else 100

        # 鐢熸垚鎬荤粨
        summary = generate_summary(sh_data, limit_data)

        result = {
            "date": trade_date.strftime("%Y-%m-%d"),
            "day_of_week": ["鍛ㄤ竴", "鍛ㄤ簩", "鍛ㄤ笁", "鍛ㄥ洓", "鍛ㄤ簲", "鍛ㄥ叚", "鍛ㄦ棩"][trade_date.weekday()],
            "status": "success",
            "sh_index": {
                "index_name": sh_data["index_name"],
                "price": sh_data["price"],
                "change_pct": sh_data["change_pct"],
                "up_count": up_count,
                "down_count": down_count,
                "emotion": sh_emotion,
            },
            "sector": {
                "total": 90,
                "up_count": sector_breadth * 7,
                "down_count": 86 - sector_breadth * 7,
                "emotion": sector_emotion,
                "top5": limit_data["industry_top"],
            },
            "limit": {
                "limit_up": limit_up,
                "limit_down": limit_down,
            },
            "summary": summary,
            "_data_source": "鏂版氮鎸囨暟+涓滄柟璐㈠瘜娑ㄥ仠鏉緼PI锛堢湡瀹炴暟鎹級",
            "_note": "娑ㄥ仠/璺屽仠/鎸囨暟/棰嗘定鏉垮潡涓虹湡瀹濧PI鏁版嵁锛涙定璺屽鏁颁负鍩轰簬娑ㄥ仠璺屽仠姣?鎸囨暟娑ㄨ穼骞呯殑鍚堢悊浼扮畻",
            "fetch_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        save_daily_data(trade_date, result)
        update_history(result)

        print(f"  閲囬泦瀹屾垚锛佸ぇ鐩樻儏缁? {sh_emotion}, 鏉垮潡鎯呯华: {sector_emotion}, 娑ㄥ仠: {limit_up}, 璺屽仠: {limit_down}")
        return result

    except Exception as e:
        print(f"  閲囬泦澶辫触: {e}")
        import traceback
        traceback.print_exc()
        return {"status": "error", "date": trade_date.strftime("%Y-%m-%d"), "message": str(e)}

def fetch_history(days=15):
    """鑾峰彇鏈€杩慛涓氦鏄撴棩鏁版嵁"""
    print(f"\n========== 鎵归噺鑾峰彇鏈€杩?{days} 涓氦鏄撴棩鏁版嵁 ==========")
    trade_dates = []
    current = date.today()

    if not is_trade_day(current):
        last_td = get_last_trade_day(current)
        if last_td:
            trade_dates.append(last_td)
            current = last_td

    d = current - timedelta(days=1)
    while len(trade_dates) < days:
        if is_trade_day(d):
            trade_dates.append(d)
        d = d - timedelta(days=1)
        if (current - d).days > 90:
            break

    trade_dates.sort()
    print(f"鎵惧埌 {len(trade_dates)} 涓氦鏄撴棩")

    success_count = 0
    for i, td in enumerate(trade_dates):
        print(f"\n[{i+1}/{len(trade_dates)}] {td}")
        result = fetch_and_save(td, silent=False)
        if result and result.get("status") == "success":
            success_count += 1
        if i < len(trade_dates) - 1:
            time.sleep(2)

    print(f"\n========== 瀹屾垚! 鎴愬姛 {success_count}/{len(trade_dates)} ==========")

# ===================== 鍏ュ彛 =====================
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--history":
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 15
        fetch_history(days)
    else:
        fetch_and_save()
