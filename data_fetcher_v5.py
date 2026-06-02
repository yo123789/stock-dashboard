#!/usr/bin/env python

# -*- coding: utf-8 -*-

"""èä¸æ¸¸èµæç»ªçæ§ä»ªè¡¨ç - æ°æ®éé v5"""



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



# ======================== æ°æ®éé ========================



def fetch_index():

    print("[1/8] ä¸è¯ææ°...")

    try:

        df = ak.stock_zh_index_spot_em()

        sh = df[df['åç§°'] == 'ä¸è¯ææ°']

        if not sh.empty:

            r = sh.iloc[0]

            vol = safe_float(r.get('æäº¤é¢', 0)) / 1e8

            return {"price": safe_float(r['ææ°ä»·']), "change_pct": safe_float(r['æ¶¨è·å¹']), "volume": round(vol, 1)}

    except: pass

    try:

        df = ak.stock_zh_index_daily_em(symbol="sh000001")

        r = df.iloc[-1]

        return {"price": safe_float(r['close']), "change_pct": safe_float(r.get('pct_chg', 0)), "volume": 0}

    except:

        return {"price": 0, "change_pct": 0, "volume": 0}



def fetch_limit_pools():

    print("[2/8] æ¶¨åæ¿æ°æ®...")

    d = today_str()

    result = {"up": [], "down": [], "blasted": [], "continuous": []}

    for pool, key, fn in [

        ("æ¶¨å", "up", lambda: ak.stock_zt_pool_em(date=d)),

        ("è·å", "down", lambda: ak.stock_zt_pool_dtgc_em(date=d)),

        ("ç¸æ¿", "blasted", lambda: ak.stock_zt_pool_zbgc_em(date=d)),

        ("è¿æ¿", "continuous", lambda: ak.stock_zt_pool_strong_em(date=d)),

    ]:

        try:

            df = fn()

            if df is None or df.empty: continue

            for _, r in df.iterrows():

                item = {

                    "code": str(r.get('ä»£ç ', '')),

                    "name": str(r.get('åç§°', '')),

                    "change_pct": safe_float(r.get('æ¶¨è·å¹', 0)),

                }

                if key in ("up", "continuous"):

                    item["board"] = safe_int(r.get('è¿æ¿æ°', 1))

                    item["turnover"] = safe_float(r.get('æ¢æç', 0))

                    item["first_time"] = str(r.get('é¦æ¬¡å°æ¿æ¶é´', '')) if r.get('é¦æ¬¡å°æ¿æ¶é´') is not None else ''

                    item["amount"] = round(safe_float(r.get('æäº¤é¢', 0)) / 1e8, 2)

                    if key == "continuous":

                        item["style"] = "ä¸å­" if safe_float(r.get('æ¢æç', 99)) < 0.5 else "æ¢æ"

                if key == "blasted":

                    item["turnover"] = safe_float(r.get('æ¢æç', 0))

                    item["amount"] = round(safe_float(r.get('æäº¤é¢', 0)) / 1e8, 2)

                result[key].append(item)

            print(f"  {pool}: {len(result[key])}åª")

        except Exception as e:

            print(f"  {pool} error: {e}")

    return result



def fetch_sectors():

    print("[3/8] æ¿åæ°æ®...")

    result = {"top5": [], "bottom3": []}

    try:

        df = ak.stock_board_industry_summary_ths()

        if df is None or df.empty: return result

        print(f"  Sector columns: {list(df.columns)}")

        name_col = None

        pct_col = None

        leader_col = None

        leader_pct_col = None

        for c in df.columns:

            if 'åç§°' in str(c) or 'æ¿å' in str(c) or 'name' in str(c).lower():

                if name_col is None: name_col = c

            if 'æ¶¨è·å¹' in str(c) or 'pct' in str(c).lower():

                if pct_col is None and 'é¢' not in str(c): pct_col = c

            if 'é¢æ¶¨' in str(c) or 'é¾å¤´' in str(c) or 'leader' in str(c).lower():

                if 'æ¶¨å¹' in str(c) or 'pct' in str(c).lower():

                    leader_pct_col = c

                elif leader_col is None:

                    leader_col = c

        if name_col is None: name_col = df.columns[0]

        if pct_col is None: pct_col = df.columns[1] if len(df.columns) > 1 else df.columns[0]

        df = df.sort_values(pct_col, ascending=False)

        for i, (_, r) in enumerate(df.iterrows()):

            item = {

                "name": str(r[name_col]),

                "change_pct": safe_float(r[pct_col]),

                "up_count": 0,

                "down_count": 0,

                "leader": str(r.get(leader_col, '')) if leader_col else '',

                "leader_pct": safe_float(r.get(leader_pct_col, 0)) if leader_pct_col else 0,

            }

            if i < 5: result["top5"].append(item)

            elif i >= len(df) - 3: result["bottom3"].append(item)

    except Exception as e:

        print(f"  Sector error: {e}")

        # fallback

        try:

            df2 = ak.stock_board_concept_name_em()

            if df2 is not None and not df2.empty:

                df2 = df2.sort_values('æ¶¨è·å¹', ascending=False)

                for i, (_, r) in enumerate(df2.iterrows()):

                    item = {

                        "name": str(r['æ¿ååç§°']),

                        "change_pct": safe_float(r['æ¶¨è·å¹']),

                        "up_count": 0, "down_count": 0,

                        "leader": "",

                        "leader_pct": 0,

                    }

                    if i < 5: result["top5"].append(item)

                    elif i >= len(df2) - 3: result["bottom3"].append(item)

        except Exception as e2:

            print(f"  Fallback sector error: {e2}")

    return result



def fetch_north_flow():

    print("[4/8] ååèµé...")

    try:

        df = ak.stock_hsgt_north_net_flow_in_em(symbol="åä¸")

        if df is not None and not df.empty:

            r = df.iloc[-1]

            return safe_float(r.get('å½æ¥èµéåæµå¥', 0))

    except: pass

    # å°è¯å®æ¶æ¥å£

    try:

        df = ak.stock_hsgt_north_net_flow_in_real_em()

        if df is not None and not df.empty:

            r = df.iloc[-1]

            return safe_float(r.get('åæµå¥', 0))

    except: pass

    return 0



def fetch_dragon_tiger():

    print("[5/8] é¾èæ¦...")

    result = []

    try:

        df = ak.stock_lhb_detail_em()

        if df is not None and not df.empty:

            for _, r in df.head(30).iterrows():

                result.append({

                    "code": str(r.get('ä»£ç ', '')),

                    "name": str(r.get('åç§°', '')),

                    "change_pct": safe_float(r.get('æ¶¨è·å¹', 0)),

                    "buy": round(safe_float(r.get('ä¹°æ¹ä¹°å¥é¢', 0)), 2),

                    "sell": round(safe_float(r.get('åæ¹ååºé¢', 0)), 2),

                    "reason": str(r.get('ä¸æ¦åå ', '')),

                })

    except Exception as e:

        print(f"  Dragon tiger error: {e}")

    return result



def fetch_emotion_history():

    """è¿10æ¥æç»ªåå²"""

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



# ======================== æç»ªè®¡ç® ========================



def calc_emotion(index_data, pools):

    """ç»¼åæç»ªè¯å 0-100"""

    if not pools["up"]:

        return {"score": 0, "phase": "éäº¤ææ¥", "position": "ç©ºä»", "detail": {}}



    zt = len(pools["up"])

    dt = len(pools["down"])

    zb = len(pools["blasted"])

    lb = len(pools["continuous"])



    # æ¶¨è·æ¯

    total_limit = zt + dt

    if total_limit > 0:

        ratio = zt / total_limit

    else:

        ratio = 0.5



    # ç¸æ¿ç

    total_attempt = zt + zb

    blast_rate = zb / total_attempt if total_attempt > 0 else 0



    # è¿æ¿å¼ºåº¦ï¼è¿æ¿è¡å æ¶¨åæ¯ï¼

    lb_ratio = lb / zt if zt > 0 else 0



    # ææ°è´¡ç®

    idx_pct = index_data.get("change_pct", 0)

    idx_score = min(max((idx_pct + 2) / 4 * 100, 0), 100)



    # ç»¼åè¯å

    score = ratio * 40 + (1 - blast_rate) * 25 + lb_ratio * 20 + idx_score * 0.15



    # è°æ´

    if zt > 100:

        score = min(score + 10, 100)

    if dt > 50:

        score = max(score - 15, 0)



    score = round(min(max(score, 0), 100))



    # é¶æ®µå¤æ­

    if score >= 80: phase = "ä¸»åæµªã»å¼ºä¸è´"

    elif score >= 65: phase = "éè¡åå¼ºã»å¯æä½"

    elif score >= 50: phase = "åæ­§å å¤§ã»è°¨æ"

    elif score >= 35: phase = "éæ½®åæã»åä»"

    else: phase = "å°ç¹ã»é²å®"



    # ä»ä½å»ºè®®

    if score >= 80: position = "8-10æ"

    elif score >= 65: position = "5-7æ"

    elif score >= 50: position = "3-4æ"

    elif score >= 35: position = "1-2æ"

    else: position = "ç©ºä»"



    # ç¸æ¿ç

    b_rate = round(blast_rate * 100, 1)



    # å¤§é¢è¡ï¼ç¸æ¿è¡ä¸­è·å¹å¤§çï¼

    big_noodles = 0

    for b in pools["blasted"]:

        if b.get("change_pct", 0) < -5:

            big_noodles += 1



    # è¿æ¿æçº§æåçï¼æè¿ç»­æ¶¨åæ°æ®çï¼ç2æ¿ä»¥ä¸æçº§ï¼

    board2_up = 0

    board2_cnt = 0

    for c in pools["continuous"]:

        if c.get("board", 0) >= 2:

            board2_cnt += 1

            if c.get("change_pct", 0) > 9:

                board2_up += 1

    promotion = round(board2_up / board2_cnt * 100, 1) if board2_cnt > 0 else 0



    # æ¨æ¥è¿æ¿æ¶¨å¹ï¼ç¨è¿ç»­æ¶¨ååè¡¨çæ¶¨è·å¹å¹³åï¼

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



# ======================== è¿æ¿æ¢¯é ========================



def build_ladder(pools):

    """ææ¿é«æåºçè¿æ¿æ¢¯é"""

    ladder = {}

    for c in pools["continuous"]:

        b = c.get("board", 1)

        if b < 2: continue

        if b not in ladder:

            ladder[b] = []

        ladder[b].append(c)



    result = []

    for b in sorted(ladder.keys(), reverse=True):

        for stock in ladder[b]:

            result.append(stock)

    return result



def get_max_board(ladder):

    if not ladder:

        return 0

    return max(s.get("board", 0) for s in ladder)



# ======================== æ¶¨è·åæå ========================



def split_limits(pools):

    up = pools["up"]

    down = pools["down"]

    # ç®ååç±»

    up_20cm = sum(1 for s in up if s.get("change_pct", 0) > 19)

    down_20cm = sum(1 for s in down if s.get("change_pct", 0) < -19)

    # ä¸­åæ¶¨åï¼æäº¤é¢>5äº¿ï¼

    up_main = sum(1 for s in up if s.get("amount", 0) > 5)

    # é«ä½è¡è·åï¼è¿æ¿è¿çè·åè¡ï¼ç¨åç§°è¿ä¼¼å¤æ­ï¼ã

    # æ´ä¸¥è°¨ï¼è·åè¡ä¸­åææè¿è¿æ¿ç

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



# ======================== å¼å¨æ£æµ ========================



def detect_events(current_pools, events_file):

    """ä¸ä¸æ¬¡æ°æ®å¯¹æ¯æ£æµå¼å¨"""

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



    # æ°ç¸æ¿

    new_blast = now_zb - prev_zb

    for s in current_pools["blasted"]:

        if s["code"] in new_blast:

            events.append({"time": now, "type": "blast", "msg": f"{s['name']} ç¸æ¿"})



    # æ°è·å

    new_dt = now_dt - prev.get("dt_codes", set())

    for s in current_pools["down"]:

        if s["code"] in new_dt:

            events.append({"time": now, "type": "limit_down", "msg": f"{s['name']} è·å"})



    # ä¿å­å½åç¶æç¨äºä¸æ¬¡å¯¹æ¯

    with open(events_file, "w", encoding="utf-8") as f:

        json.dump({

            "up_codes": list(now_up),

            "zb_codes": list(now_zb),

            "dt_codes": list(now_dt),

        }, f, ensure_ascii=False)



    # åå¹¶åå²äºä»¶

    try:

        all_events_file = events_file.replace(".json", "_all.json")

        if os.path.exists(all_events_file):

            with open(all_events_file, "r", encoding="utf-8") as f:

                old_events = json.load(f)

            events = old_events[-50:] + events  # ä¿çæè¿50æ¡

    except: pass



    return events[-30:]  # è¿åæè¿30æ¡



# ======================== ä¸»æµç¨ ========================



def main():

    print(f"========== {now_str()} å¼å§éé ==========")



    index_data = fetch_index()

    if not index_data:

        print("ERROR: æ æ³è·åææ°æ°æ®")

        return



    pools = fetch_limit_pools()

    sectors = fetch_sectors()

    north = fetch_north_flow()

    dragon = fetch_dragon_tiger()

    history_emotion = fetch_emotion_history()



    print("[6/8] æç»ªè¯å...")

    emotion = calc_emotion(index_data, pools)

    ladder = build_ladder(pools)

    max_board = get_max_board(ladder)

    limit_split = split_limits(pools)



    print("[7/8] å¼å¨æ£æµ...")

    events = detect_events(pools, os.path.join(BASE, "events_snapshot.json"))



    # æå»ºè¾åº

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



    print("[8/8] ä¿å­...")

    with open(DASHBOARD_FILE, "w", encoding="utf-8") as f:

        json.dump(dashboard, f, ensure_ascii=False, indent=2)

    print(f"  â {DASHBOARD_FILE}")



    # æ¶çåè¿½å å°åå²

    now = datetime.now().time()

    if now >= time(15, 5):

        print("  æ¶çæ¨¡å¼ï¼è¿½å åå²...")

        history = []

        if os.path.exists(HISTORY_FILE):

            with open(HISTORY_FILE, "r", encoding="utf-8") as f:

                history = json.load(f)

        # å»é

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

        print(f"  â {HISTORY_FILE} ({len(history)} days)")



    # æ±æ»

    e = emotion

    print(f"\n========== ééå®æ ==========")

    print(f"  ææ°: {index_data['price']:.2f} ({index_data['change_pct']:+.2f}%)")

    print(f"  æç»ª: {e['score']}å [{e['phase']}] å»ºè®®: {e['position']}")

    print(f"  æ¶¨å: {e['detail']['zt_count']} | è·å: {e['detail']['dt_count']} | ç¸æ¿: {e['detail']['zb_count']}")

    print(f"  ç¸æ¿ç: {e['detail']['blast_rate']}% | æçº§ç: {e['detail']['promotion_rate']}%")

    print(f"  æé«æ¿: {max_board}æ¿ | å¤§é¢è¡: {e['detail']['noodle_count']}åª")

    print(f"  åå: {north:+.2f}äº¿")



if __name__ == "__main__":

    main()

