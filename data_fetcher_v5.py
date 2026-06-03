#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""职业游资情绪监控仪表盘 - 数据采集 v5"""

import akshare as ak
import json, os, sys
from datetime import datetime, time, timedelta

BASE = os.path.dirname(os.path.abspath(__file__))
DASHBOARD_FILE = os.path.join(BASE, "dashboard_data.json")
HISTORY_FILE = os.path.join(BASE, "history_v5.json")
MAX_HISTORY = 60

def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def today_str():
    return datetime.now().strftime("%Y%m%d")

def date_dash():
    return datetime.now().strftime("%Y-%m-%d")

def safe_float(v, default=0):
    try: return round(float(v), 2)
    except: return default

def safe_int(v, default=0):
    try: return int(float(v))
    except: return default

# ======================== 数据采集 ========================

def fetch_index():
    print("[1/8] 上证指数...")
    # Try spot first, fallback to daily
    try:
        df = ak.stock_zh_index_spot_em()
        sh = df[df['名称'] == '上证指数']
        if not sh.empty:
            r = sh.iloc[0]
            vol = safe_float(r.get('成交额', 0)) / 1e8
            price = safe_float(r['最新价'])
            pct = safe_float(r['涨跌幅'])
            if price > 0:
                return {"price": price, "change_pct": pct, "volume": round(vol, 1)}
    except: pass
    try:
        df = ak.stock_zh_index_daily(symbol="sh000001")
        if len(df) >= 2:
            r = df.iloc[-1]
            prev = df.iloc[-2]
            price = safe_float(r['close'])
            pct = round((r['close'] - prev['close']) / prev['close'] * 100, 2)
            vol = safe_float(r['volume']) / 1e8
            return {"price": price, "change_pct": pct, "volume": max(round(vol, 1), 0)}
    except:
        # Last resort: load from history
        try:
            if os.path.exists(HISTORY_FILE):
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    h = json.load(f)
                if h:
                    mk = h[0].get("market", {})
                    if mk.get("price", 0) > 0:
                        print(f"  Using history market: {mk['price']}")
                        return mk
        except: pass
        return {"price": 0, "change_pct": 0, "volume": 0}

def fetch_limit_pools():
    print("[2/8] 涨停板数据...")
    d = today_str()
    result = {"up": [], "down": [], "blasted": [], "continuous": []}
    for pool, key, fn in [
        ("涨停", "up", lambda: ak.stock_zt_pool_em(date=d)),
        ("跌停", "down", lambda: ak.stock_zt_pool_dtgc_em(date=d)),
        ("炸板", "blasted", lambda: ak.stock_zt_pool_zbgc_em(date=d)),
        ("连板", "continuous", lambda: ak.stock_zt_pool_strong_em(date=d)),
    ]:
        try:
            df = fn()
            if df is None or df.empty: continue
            for _, r in df.iterrows():
                item = {
                    "code": str(r.get('代码', '')),
                    "name": str(r.get('名称', '')),
                    "change_pct": safe_float(r.get('涨跌幅', 0)),
                }
                if key in ("up", "continuous"):
                    item["board"] = safe_int(r.get('连板数', 1))
                    item["turnover"] = safe_float(r.get('换手率', 0))
                    item["first_time"] = str(r.get('首次封板时间', '')) if r.get('首次封板时间') is not None else ''
                    item["amount"] = round(safe_float(r.get('成交额', 0)) / 1e8, 2)
                    if key == "continuous":
                        item["style"] = "一字" if safe_float(r.get('换手率', 99)) < 0.5 else "换手"
                if key == "blasted":
                    item["turnover"] = safe_float(r.get('换手率', 0))
                    item["amount"] = round(safe_float(r.get('成交额', 0)) / 1e8, 2)
                result[key].append(item)
            print(f"  {pool}: {len(result[key])}只")
        except Exception as e:
            print(f"  {pool} error: {e}")
    return result

def fetch_sectors():
    print("[3/8] 板块数据...")
    result = {"top5": [], "bottom3": []}
    try:
        df = ak.stock_board_industry_summary_ths()
        if df is None or df.empty: return result
        cols = list(df.columns)
        print(f"  Sector columns: {cols}")

        # Hardware-verified column names for akshare stock_board_industry_summary_ths:
        # ['序号', '板块', '涨跌幅', '总成交量', '总成交额', '净流入', '上涨家数', '下跌家数', '均价', '领涨股', '领涨股-最新价', '领涨股-涨跌幅']
        name_col = None
        pct_col = None
        up_col = None
        down_col = None
        leader_col = None
        leader_pct_col = None
        
        for c in cols:
            cs = str(c)
            if cs == '板块':
                name_col = c
            elif cs == '涨跌幅':
                pct_col = c
            elif cs == '上涨家数':
                up_col = c
            elif cs == '下跌家数':
                down_col = c
            elif cs == '领涨股':
                leader_col = c
            elif cs == '领涨股-涨跌幅':
                leader_pct_col = c

        df_sorted = df.sort_values(pct_col, ascending=False, na_position='last')
        for i, (_, r) in enumerate(df_sorted.iterrows()):
            n = str(r[name_col])
            p = safe_float(r[pct_col])
            if n == '' or n == 'nan': continue
            item = {
                "name": n, "change_pct": p,
                "count_up": safe_int(r[up_col]) if up_col else 0,
                "count_down": safe_int(r[down_col]) if down_col else 0,
                "leader": str(r[leader_col]) if leader_col else "",
                "leader_pct": safe_float(r[leader_pct_col]) if leader_pct_col else 0,
            }
            if i < 5: result["top5"].append(item)
            elif i >= len(df_sorted) - 3: result["bottom3"].append(item)
        print(f"  Top5: {[s['name'] for s in result['top5']]}")
    except Exception as e:
        print(f"  Sector error: {e}")
    return result

def fetch_north_flow():
    print("[4/8] 北向资金...")
    try:
        df = ak.stock_hsgt_north_net_flow_in_em(symbol="北上")
        if df is not None and not df.empty:
            r = df.iloc[-1]
            return safe_float(r.get('当日资金净流入', 0))
    except: pass
    # 尝试实时接口
    try:
        df = ak.stock_hsgt_north_net_flow_in_real_em()
        if df is not None and not df.empty:
            r = df.iloc[-1]
            return safe_float(r.get('净流入', 0))
    except: pass
    return 0

def fetch_dragon_tiger():
    print("[5/8] 龙虎榜...")
    result = []
    try:
        from datetime import datetime, timedelta
        end = datetime.now().strftime("%Y%m%d")
        start = (datetime.now() - timedelta(days=5)).strftime("%Y%m%d")
        df = ak.stock_lhb_detail_em(start_date=start, end_date=end)
        if df is not None and not df.empty:
            # Get latest trading date from data
            if '上榜日' in df.columns:
                df['上榜日'] = df['上榜日'].astype(str)
                latest_date = df['上榜日'].max()
                df = df[df['上榜日'] == latest_date]
                print(f"  Dragon tiger date: {latest_date}")
            for _, r in df.head(30).iterrows():
                buy_val = safe_float(r.get('龙虎榜买入额', 0))
                sell_val = safe_float(r.get('龙虎榜卖出额', 0))
                result.append({
                    "code": str(r.get('代码', '')),
                    "name": str(r.get('名称', '')),
                    "change_pct": safe_float(r.get('涨跌幅', 0)),
                    "buy": round(buy_val / 1e4, 2),
                    "sell": round(sell_val / 1e4, 2),
                    "reason": str(r.get('上榜原因', '')),
                })
            print(f"  Dragon tiger: {len(result)} entries")
    except Exception as e:
        print(f"  Dragon tiger error: {e}")
    return result

def fetch_emotion_history():
    """近10日情绪历史"""
    result = []
    try:
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)
            for h in history[-10:]:
                result.append({
                    "date": h.get("date", ""),
                    "score": h.get("emotion", {}).get("score", 0),
                })
    except: pass
    return result

# ======================== 情绪计算 ========================

def calc_emotion(index_data, pools):
    """综合情绪评分 0-100"""
    if not pools["up"]:
        return {"score": 0, "phase": "非交易日", "position": "空仓", "detail": {}}

    zt = len(pools["up"])
    dt = len(pools["down"])
    zb = len(pools["blasted"])
    lb = len(pools["continuous"])

    # 涨跌比
    total_limit = zt + dt
    if total_limit > 0:
        ratio = zt / total_limit
    else:
        ratio = 0.5

    # 炸板率
    total_attempt = zt + zb
    blast_rate = zb / total_attempt if total_attempt > 0 else 0

    # 连板强度（连板股占涨停比）
    lb_ratio = lb / zt if zt > 0 else 0

    # 指数贡献
    idx_pct = index_data.get("change_pct", 0)
    idx_score = min(max((idx_pct + 2) / 4 * 100, 0), 100)

    # 综合评分
    score = ratio * 40 + (1 - blast_rate) * 25 + min(lb_ratio, 1) * 20 + idx_score * 0.15

    # 调整
    if zt > 100:
        score = min(score + 10, 100)
    if dt > 50:
        score = max(score - 15, 0)

    score = round(min(max(score, 0), 100))

    # 阶段判断
    if score >= 80: phase = "主升浪・强一致"
    elif score >= 65: phase = "震荡偏强・可操作"
    elif score >= 50: phase = "分歧加大・谨慎"
    elif score >= 35: phase = "退潮初期・减仓"
    else: phase = "冰点・防守"

    # 仓位建议
    if score >= 80: position = "8-10成"
    elif score >= 65: position = "5-7成"
    elif score >= 50: position = "3-4成"
    elif score >= 35: position = "1-2成"
    else: position = "空仓"

    # 炸板率
    b_rate = round(blast_rate * 100, 1)

    # 大面股（炸板股中跌幅大的）
    big_noodles = 0
    for b in pools["blasted"]:
        if b.get("change_pct", 0) < -5:
            big_noodles += 1

    # 连板晋级成功率（有连续涨停数据的，看2板以上晋级）
    board2_up = 0
    board2_cnt = 0
    for c in pools["continuous"]:
        if c.get("board", 0) >= 2:
            board2_cnt += 1
            if c.get("change_pct", 0) > 9:
                board2_up += 1
    promotion = round(board2_up / board2_cnt * 100, 1) if board2_cnt > 0 else 0

    # 昨日连板涨幅（用连续涨停列表的涨跌幅平均）
    lb_pct_sum = sum(c.get("change_pct", 0) for c in pools["continuous"])
    lb_pct_avg = round(lb_pct_sum / len(pools["continuous"]), 1) if pools["continuous"] else 0

    return {
        "score": score,
        "phase": phase,
        "position": position,
        "detail": {
            "blast_rate": b_rate,
            "prev_connect_pct": lb_pct_avg,
            "noodle_count": big_noodles,
            "promotion_rate": promotion,
            "zt_count": zt,
            "dt_count": dt,
            "zb_count": zb,
            "lb_count": lb,
        }
    }

# ======================== 连板梯队 ========================

def build_ladder(pools):
    """按板高排序的连板梯队"""
    ladder = {}
    for c in pools["continuous"]:
        b = c.get("board", 1)
        # Include all continuous stocks, filter only if high-boards exist
        if b not in ladder:
            ladder[b] = []
        ladder[b].append(c)
    
    # If we have board>=2 stocks, only show those; otherwise show all
    high_keys = [k for k in ladder.keys() if k >= 2]
    keys = high_keys if high_keys else list(ladder.keys())

    result = []
    for b in sorted(keys, reverse=True):
        for stock in ladder[b]:
            result.append(stock)
    return result

def get_max_board(ladder):
    if not ladder:
        return 0
    return max(s.get("board", 0) for s in ladder)

# ======================== 涨跌停拆分 ========================

def split_limits(pools):
    up = pools["up"]
    down = pools["down"]
    # 简单分类
    up_20cm = sum(1 for s in up if s.get("change_pct", 0) > 19)
    down_20cm = sum(1 for s in down if s.get("change_pct", 0) < -19)
    # 中军涨停（成交额>5亿）
    up_main = sum(1 for s in up if s.get("amount", 0) > 5)
    # 高位股跌停（连板过的跌停股，用名称近似判断）。
    # 更严谨：跌停股中前期有过连板的
    down_high = 0
    for s in down:
        for c in pools["continuous"]:
            if s["code"] == c["code"]:
                down_high += 1
                break
    return {
        "total_up": len(up),
        "total_down": len(down),
        "up_20cm": up_20cm,
        "down_20cm": down_20cm,
        "up_main_force": up_main,
        "down_high": down_high,
    }

# ======================== 异动检测 ========================

def detect_events(current_pools, events_file):
    """与上次数据对比检测异动"""
    events = []
    prev = {}
    try:
        if os.path.exists(events_file):
            with open(events_file, "r", encoding="utf-8") as f:
                prev = json.load(f)
    except: pass

    prev_up = set(prev.get("up_codes", []))
    prev_zb = set(prev.get("zb_codes", []))
    now_up = set(s["code"] for s in current_pools["up"])
    now_zb = set(s["code"] for s in current_pools["blasted"])
    now_dt = set(s["code"] for s in current_pools["down"])

    now = datetime.now().strftime("%H:%M")

    # 新炸板
    new_blast = now_zb - prev_zb
    for s in current_pools["blasted"]:
        if s["code"] in new_blast:
            events.append({"time": now, "type": "blast", "msg": f"{s['name']} 炸板"})

    # 新跌停
    new_dt = now_dt - prev.get("dt_codes", set())
    for s in current_pools["down"]:
        if s["code"] in new_dt:
            events.append({"time": now, "type": "limit_down", "msg": f"{s['name']} 跌停"})

    # 保存当前状态用于下次对比
    with open(events_file, "w", encoding="utf-8") as f:
        json.dump({
            "up_codes": list(now_up),
            "zb_codes": list(now_zb),
            "dt_codes": list(now_dt),
        }, f, ensure_ascii=False)

    # 合并历史事件
    try:
        all_events_file = events_file.replace(".json", "_all.json")
        if os.path.exists(all_events_file):
            with open(all_events_file, "r", encoding="utf-8") as f:
                old_events = json.load(f)
            events = old_events[-50:] + events  # 保留最近50条
    except: pass

    return events[-30:]  # 返回最近30条

# ======================== 主流程 ========================

def main():
    print(f"========== {now_str()} 开始采集 ==========")

    index_data = fetch_index()
    if not index_data:
        print("ERROR: 无法获取指数数据")
        return

    pools = fetch_limit_pools()
    sectors = fetch_sectors()
    north = fetch_north_flow()
    dragon = fetch_dragon_tiger()
    history_emotion = fetch_emotion_history()

    print("[6/8] 情绪评分...")
    emotion = calc_emotion(index_data, pools)
    ladder = build_ladder(pools)
    max_board = get_max_board(ladder)
    limit_split = split_limits(pools)

    print("[7/8] 异动检测...")
    events = detect_events(pools, os.path.join(BASE, "events_snapshot.json"))

    # 构建输出
    dashboard = {
        "timestamp": now_str(),
        "date": date_dash(),
        "market": index_data,
        "emotion": emotion,
        "core": {
            "blast_rate": emotion["detail"]["blast_rate"],
            "prev_connect_pct": emotion["detail"]["prev_connect_pct"],
            "noodle_count": emotion["detail"]["noodle_count"],
            "promotion_rate": emotion["detail"]["promotion_rate"],
        },
        "ladder": {
            "max_board": max_board,
            "stocks": ladder,
        },
        "limits": limit_split,
        "sectors": sectors,
        "north_flow": north,
        "dragon_tiger": dragon,
        "events": events,
        "history_emotion": history_emotion,
    }

    print("[8/8] 保存...")
    with open(DASHBOARD_FILE, "w", encoding="utf-8") as f:
        json.dump(dashboard, f, ensure_ascii=False, indent=2)
    print(f"  → {DASHBOARD_FILE}")

    # 收盘后追加到历史
    now = datetime.now().time()
    if now >= time(15, 5):
        print("  收盘模式：追加历史...")
        history = []
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)
        # 去重
        history = [h for h in history if h.get("date") != date_dash()]
        history.append({
            "date": date_dash(),
            "market": index_data,
            "emotion": emotion,
            "core": dashboard["core"],
            "ladder": dashboard["ladder"],
            "limits": limit_split,
            "sectors": sectors,
            "dragon_tiger": dragon,
        })
        history.sort(key=lambda x: x["date"], reverse=True)
        if len(history) > MAX_HISTORY:
            history = history[:MAX_HISTORY]
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
        print(f"  → {HISTORY_FILE} ({len(history)} days)")

    # 汇总
    e = emotion
    print(f"\n========== 采集完成 ==========")
    print(f"  指数: {index_data['price']:.2f} ({index_data['change_pct']:+.2f}%)")
    print(f"  情绪: {e['score']}分 [{e['phase']}] 建议: {e['position']}")
    print(f"  涨停: {e['detail']['zt_count']} | 跌停: {e['detail']['dt_count']} | 炸板: {e['detail']['zb_count']}")
    print(f"  炸板率: {e['detail']['blast_rate']}% | 晋级率: {e['detail']['promotion_rate']}%")
    print(f"  最高板: {max_board}板 | 大面股: {e['detail']['noodle_count']}只")
    print(f"  北向: {north:+.2f}亿")

if __name__ == "__main__":
    main()
