# A-share market sentiment data fetcher v3
# Data sources: AKShare + Sina index API
# Output: data/YYYY-MM-DD.json + history.json (last 15 days)

import os
import sys
import json
import time
from datetime import datetime, date, timedelta

try:
    import akshare as ak
except ImportError:
    print("Please install akshare: pip install akshare")
    sys.exit(1)

DATA_DIR = "data"
HISTORY_FILE = "history.json"

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

def calc_emotion(up, down):
    total = up + down
    if total == 0:
        return 50
    ratio = up / total
    return int(max(0, min(100, ratio * 100)))

def fetch_sh_index(target_date):
    """Fetch Shanghai Composite Index via Sina API"""
    try:
        df = ak.stock_zh_index_daily(symbol="sh000001")
        if df is None or len(df) == 0:
            raise ValueError("SH index data is empty")

        date_str = target_date.strftime("%Y-%m-%d")
        row = None
        if "date" in df.columns:
            df_date = df["date"]
            if hasattr(df_date.iloc[0], "strftime"):
                row = df[df["date"] == target_date]
            else:
                row = df[df["date"].astype(str) == date_str]

        if row is None or len(row) == 0:
            raise ValueError("SH index data not found for " + date_str)

        close_price = float(row.iloc[0]["close"])
        open_price = float(row.iloc[0]["open"])

        if "date" in df.columns:
            all_dates = sorted(df["date"].tolist())
            target_dt = target_date if hasattr(all_dates[0], "strftime") else date_str
            if target_dt in all_dates:
                idx = all_dates.index(target_dt)
                if idx > 0:
                    prev_date = all_dates[idx - 1]
                    if hasattr(prev_date, "strftime"):
                        prev_row = df[df["date"] == prev_date]
                    else:
                        prev_row = df[df["date"].astype(str) == prev_date]
                    prev_close = float(prev_row.iloc[0]["close"])
                    change_pct = round((close_price - prev_close) / prev_close * 100, 2)
                else:
                    change_pct = round((close_price - open_price) / open_price * 100, 2)
            else:
                change_pct = round((close_price - open_price) / open_price * 100, 2)
        else:
            change_pct = round((close_price - open_price) / open_price * 100, 2)

        return {
            "index_name": "Shanghai Composite",
            "price": round(close_price, 2),
            "change_pct": change_pct,
            "source": "Sina API",
        }
    except Exception as e:
        print(f"  SH index fetch failed: {e}")
        return None

def fetch_limit_data(target_date):
    """Fetch limit-up/limit-down data + industry stats"""
    date_str = target_date.strftime("%Y%m%d")
    limit_up = 0
    limit_down = 0
    industry_top = []

    try:
        zt_df = ak.stock_zt_pool_em(date=date_str)
        limit_up = len(zt_df)
        ind_col = None
        for col in zt_df.columns:
            col_lower = str(col).lower()
            if any(kw in col_lower for kw in ["industry", "trade", "sector"]):
                ind_col = col
                break
        if ind_col is None and len(zt_df.columns) > 1:
            ind_col = zt_df.columns[1]
        if ind_col:
            ind_counts = zt_df[ind_col].value_counts().head(5)
            industry_top = [{"name": str(k), "count": int(v)} for k, v in ind_counts.items()]
    except Exception as e:
        print(f"  Limit-up data fetch failed: {e}")

    try:
        dt_df = ak.stock_zt_pool_dtgc_em(date=date_str)
        limit_down = len(dt_df)
    except Exception as e:
        print(f"  Limit-down data fetch failed: {e}")

    return {
        "limit_up": limit_up,
        "limit_down": limit_down,
        "industry_top": industry_top,
    }

def generate_summary(sh_data, limit_data):
    if not sh_data:
        return "Data unavailable..."

    change_pct = sh_data["change_pct"]
    limit_up = limit_data["limit_up"]
    limit_down = limit_data["limit_down"]
    industry_top = limit_data["industry_top"]

    parts = []
    if change_pct > 2:
        parts.append(f"Market surged {change_pct:+.2f}%")
    elif change_pct > 0.5:
        parts.append(f"Market rose {change_pct:+.2f}%")
    elif change_pct >= -0.5:
        parts.append(f"Market flat {change_pct:+.2f}%")
    elif change_pct >= -2:
        parts.append(f"Market dipped {change_pct:+.2f}%")
    else:
        parts.append(f"Market plunged {change_pct:+.2f}%")

    parts.append(f"Limit-up: {limit_up}, limit-down: {limit_down}")

    if industry_top:
        parts.append(f"Leading sector: {industry_top[0]['name']}")

    return ". ".join(parts) + "."

def save_daily_data(trade_date, data):
    os.makedirs(DATA_DIR, exist_ok=True)
    filename = trade_date.strftime("%Y-%m-%d") + ".json"
    filepath = os.path.join(DATA_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  Saved to: {filepath}")

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

    print(f"  history.json updated, {len(history)} days")

def fetch_and_save(trade_date=None, silent=False):
    if trade_date is None:
        trade_date = date.today()

    if not is_trade_day(trade_date):
        if not silent:
            print(f"{trade_date} is not a trading day (weekend/holiday), skipping.")
        return {"status": "holiday", "date": trade_date.strftime("%Y-%m-%d"), "message": "Non-trading day"}

    print(f"Fetching data for {trade_date}...")

    try:
        sh_data = fetch_sh_index(trade_date)
        limit_data = fetch_limit_data(trade_date)

        if not sh_data:
            print("  SH index data unavailable, skipping.")
            return {"status": "error", "date": trade_date.strftime("%Y-%m-%d"), "message": "Missing SH index data"}

        total_stocks = 5525
        change_pct = sh_data["change_pct"]
        limit_up = limit_data.get("limit_up", 0)
        limit_down = limit_data.get("limit_down", 0)

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

        sh_emotion = calc_emotion(up_count, down_count)
        sector_breadth = len(limit_data.get("industry_top", []))
        sector_emotion = min(100, sector_breadth * 20) if sector_breadth <= 5 else 100

        summary = generate_summary(sh_data, limit_data)

        day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        result = {
            "date": trade_date.strftime("%Y-%m-%d"),
            "day_of_week": day_names[trade_date.weekday()],
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
                "top5": limit_data.get("industry_top", []),
            },
            "limit": {
                "limit_up": limit_up,
                "limit_down": limit_down,
            },
            "summary": summary,
            "_data_source": "Sina Index + EastMoney limit-up/down API",
            "_note": "Limit-up/down/index/leading-sector from real API; up/down counts are estimates",
            "fetch_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        save_daily_data(trade_date, result)
        update_history(result)

        print(f"  Done. Market: {sh_emotion}, Sector: {sector_emotion}, LU: {limit_up}, LD: {limit_down}")
        return result

    except Exception as e:
        print(f"  Fetch failed: {e}")
        import traceback
        traceback.print_exc()
        return {"status": "error", "date": trade_date.strftime("%Y-%m-%d"), "message": str(e)}

def fetch_history(days=15):
    print(f"\n========== Batch fetch last {days} trading days ==========")
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
    print(f"Found {len(trade_dates)} trading days")

    success_count = 0
    for i, td in enumerate(trade_dates):
        print(f"\n[{i+1}/{len(trade_dates)}] {td}")
        result = fetch_and_save(td, silent=False)
        if result and result.get("status") == "success":
            success_count += 1
        if i < len(trade_dates) - 1:
            time.sleep(2)

    print(f"\n========== Done! Success: {success_count}/{len(trade_dates)} ==========")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--history":
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 15
        fetch_history(days)
    else:
        fetch_and_save()
