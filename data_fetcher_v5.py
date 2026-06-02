#!/usr/bin/env python



# -*- coding: utf-8 -*-



"""Ã¨ÂÂÃ¤Â¸ÂÃ¦Â¸Â¸Ã¨ÂµÂÃ¦ÂÂÃ§Â»ÂªÃ§ÂÂÃ¦ÂÂ§Ã¤Â»ÂªÃ¨Â¡Â¨Ã§ÂÂ - Ã¦ÂÂ°Ã¦ÂÂ®Ã©ÂÂÃ©ÂÂ v5"""







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







# ======================== Ã¦ÂÂ°Ã¦ÂÂ®Ã©ÂÂÃ©ÂÂ ========================







def fetch_index():

    print("[1/8] \u4e0a\u8bc1\u6307\u6570...")

    try:

        df = ak.stock_zh_index_spot_em()

        sh = df[df['\u540d\u79f0'] == '\u4e0a\u8bc1\u6307\u6570']

        if not sh.empty:

            r = sh.iloc[0]

            vol = safe_float(r.get('\u6210\u4ea4\u989d', 0)) / 1e8

            price = safe_float(r['\u6700\u65b0\u4ef7'])

            pct = safe_float(r['\u6da8\u8dcc\u5e45'])

            if price > 0:

                return {"price": price, "change_pct": pct, "volume": round(vol, 1)}

    except: pass

    try:

        df = ak.stock_zh_index_daily_em(symbol="sh000001")

        r = df.iloc[-1]

        price = safe_float(r.get('close', r.get('\u6536\u76d8', 0)))

        pct = safe_float(r.get('pct_chg', r.get('\u6da8\u8dcc\u5e45', 0)))

        vol = safe_float(r.get('volume', r.get('\u6210\u4ea4\u91cf', 0))) / 1e8 if safe_float(r.get('volume', 0)) > 1e6 else safe_float(r.get('\u6210\u4ea4\u989d', 0)) / 1e8

        return {"price": price, "change_pct": pct, "volume": max(round(vol, 1), 0)}

    except:

        return {"price": 0, "change_pct": 0, "volume": 0}

def fetch_limit_pools():



    print("[2/8] Ã¦Â¶Â¨Ã¥ÂÂÃ¦ÂÂ¿Ã¦ÂÂ°Ã¦ÂÂ®...")



    d = today_str()



    result = {"up": [], "down": [], "blasted": [], "continuous": []}



    for pool, key, fn in [



        ("Ã¦Â¶Â¨Ã¥ÂÂ", "up", lambda: ak.stock_zt_pool_em(date=d)),



        ("Ã¨Â·ÂÃ¥ÂÂ", "down", lambda: ak.stock_zt_pool_dtgc_em(date=d)),



        ("Ã§ÂÂ¸Ã¦ÂÂ¿", "blasted", lambda: ak.stock_zt_pool_zbgc_em(date=d)),



        ("Ã¨Â¿ÂÃ¦ÂÂ¿", "continuous", lambda: ak.stock_zt_pool_strong_em(date=d)),



    ]:



        try:



            df = fn()



            if df is None or df.empty: continue



            for _, r in df.iterrows():



                item = {



                    "code": str(r.get('Ã¤Â»Â£Ã§Â Â', '')),



                    "name": str(r.get('Ã¥ÂÂÃ§Â§Â°', '')),



                    "change_pct": safe_float(r.get('Ã¦Â¶Â¨Ã¨Â·ÂÃ¥Â¹Â', 0)),



                }



                if key in ("up", "continuous"):



                    item["board"] = safe_int(r.get('Ã¨Â¿ÂÃ¦ÂÂ¿Ã¦ÂÂ°', 1))



                    item["turnover"] = safe_float(r.get('Ã¦ÂÂ¢Ã¦ÂÂÃ§ÂÂ', 0))



                    item["first_time"] = str(r.get('Ã©Â¦ÂÃ¦Â¬Â¡Ã¥Â°ÂÃ¦ÂÂ¿Ã¦ÂÂ¶Ã©ÂÂ´', '')) if r.get('Ã©Â¦ÂÃ¦Â¬Â¡Ã¥Â°ÂÃ¦ÂÂ¿Ã¦ÂÂ¶Ã©ÂÂ´') is not None else ''



                    item["amount"] = round(safe_float(r.get('Ã¦ÂÂÃ¤ÂºÂ¤Ã©Â¢Â', 0)) / 1e8, 2)



                    if key == "continuous":



                        item["style"] = "Ã¤Â¸ÂÃ¥Â­Â" if safe_float(r.get('Ã¦ÂÂ¢Ã¦ÂÂÃ§ÂÂ', 99)) < 0.5 else "Ã¦ÂÂ¢Ã¦ÂÂ"



                if key == "blasted":



                    item["turnover"] = safe_float(r.get('Ã¦ÂÂ¢Ã¦ÂÂÃ§ÂÂ', 0))



                    item["amount"] = round(safe_float(r.get('Ã¦ÂÂÃ¤ÂºÂ¤Ã©Â¢Â', 0)) / 1e8, 2)



                result[key].append(item)



            print(f"  {pool}: {len(result[key])}Ã¥ÂÂª")



        except Exception as e:



            print(f"  {pool} error: {e}")



    return result







def fetch_sectors():



    print("[3/8] Ã¦ÂÂ¿Ã¥ÂÂÃ¦ÂÂ°Ã¦ÂÂ®...")



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



            if 'Ã¥ÂÂÃ§Â§Â°' in str(c) or 'Ã¦ÂÂ¿Ã¥ÂÂ' in str(c) or 'name' in str(c).lower():



                if name_col is None: name_col = c



            if 'Ã¦Â¶Â¨Ã¨Â·ÂÃ¥Â¹Â' in str(c) or 'pct' in str(c).lower():



                if pct_col is None and 'Ã©Â¢Â' not in str(c): pct_col = c



            if 'Ã©Â¢ÂÃ¦Â¶Â¨' in str(c) or 'Ã©Â¾ÂÃ¥Â¤Â´' in str(c) or 'leader' in str(c).lower():



                if 'Ã¦Â¶Â¨Ã¥Â¹Â' in str(c) or 'pct' in str(c).lower():



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



                df2 = df2.sort_values('Ã¦Â¶Â¨Ã¨Â·ÂÃ¥Â¹Â', ascending=False)



                for i, (_, r) in enumerate(df2.iterrows()):



                    item = {



                        "name": str(r['Ã¦ÂÂ¿Ã¥ÂÂÃ¥ÂÂÃ§Â§Â°']),



                        "change_pct": safe_float(r['Ã¦Â¶Â¨Ã¨Â·ÂÃ¥Â¹Â']),



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



    print("[4/8] Ã¥ÂÂÃ¥ÂÂÃ¨ÂµÂÃ©ÂÂ...")



    try:



        df = ak.stock_hsgt_north_net_flow_in_em(symbol="Ã¥ÂÂÃ¤Â¸Â")



        if df is not None and not df.empty:



            r = df.iloc[-1]



            return safe_float(r.get('Ã¥Â½ÂÃ¦ÂÂ¥Ã¨ÂµÂÃ©ÂÂÃ¥ÂÂÃ¦ÂµÂÃ¥ÂÂ¥', 0))



    except: pass



    # Ã¥Â°ÂÃ¨Â¯ÂÃ¥Â®ÂÃ¦ÂÂ¶Ã¦ÂÂ¥Ã¥ÂÂ£



    try:



        df = ak.stock_hsgt_north_net_flow_in_real_em()



        if df is not None and not df.empty:



            r = df.iloc[-1]



            return safe_float(r.get('Ã¥ÂÂÃ¦ÂµÂÃ¥ÂÂ¥', 0))



    except: pass



    return 0







def fetch_dragon_tiger():



    print("[5/8] Ã©Â¾ÂÃ¨ÂÂÃ¦Â¦Â...")



    result = []



    try:



        df = ak.stock_lhb_detail_em()



        if df is not None and not df.empty:



            for _, r in df.head(30).iterrows():



                result.append({



                    "code": str(r.get('Ã¤Â»Â£Ã§Â Â', '')),



                    "name": str(r.get('Ã¥ÂÂÃ§Â§Â°', '')),



                    "change_pct": safe_float(r.get('Ã¦Â¶Â¨Ã¨Â·ÂÃ¥Â¹Â', 0)),



                    "buy": round(safe_float(r.get('Ã¤Â¹Â°Ã¦ÂÂ¹Ã¤Â¹Â°Ã¥ÂÂ¥Ã©Â¢Â', 0)), 2),



                    "sell": round(safe_float(r.get('Ã¥ÂÂÃ¦ÂÂ¹Ã¥ÂÂÃ¥ÂÂºÃ©Â¢Â', 0)), 2),



                    "reason": str(r.get('Ã¤Â¸ÂÃ¦Â¦ÂÃ¥ÂÂÃ¥ÂÂ ', '')),



                })



    except Exception as e:



        print(f"  Dragon tiger error: {e}")



    return result







def fetch_emotion_history():



    """Ã¨Â¿Â10Ã¦ÂÂ¥Ã¦ÂÂÃ§Â»ÂªÃ¥ÂÂÃ¥ÂÂ²"""



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







# ======================== Ã¦ÂÂÃ§Â»ÂªÃ¨Â®Â¡Ã§Â®Â ========================







def calc_emotion(index_data, pools):



    """Ã§Â»Â¼Ã¥ÂÂÃ¦ÂÂÃ§Â»ÂªÃ¨Â¯ÂÃ¥ÂÂ 0-100"""



    if not pools["up"]:



        return {"score": 0, "phase": "Ã©ÂÂÃ¤ÂºÂ¤Ã¦ÂÂÃ¦ÂÂ¥", "position": "Ã§Â©ÂºÃ¤Â»Â", "detail": {}}







    zt = len(pools["up"])



    dt = len(pools["down"])



    zb = len(pools["blasted"])



    lb = len(pools["continuous"])







    # Ã¦Â¶Â¨Ã¨Â·ÂÃ¦Â¯Â



    total_limit = zt + dt



    if total_limit > 0:



        ratio = zt / total_limit



    else:



        ratio = 0.5







    # Ã§ÂÂ¸Ã¦ÂÂ¿Ã§ÂÂ



    total_attempt = zt + zb



    blast_rate = zb / total_attempt if total_attempt > 0 else 0







    # Ã¨Â¿ÂÃ¦ÂÂ¿Ã¥Â¼ÂºÃ¥ÂºÂ¦Ã¯Â¼ÂÃ¨Â¿ÂÃ¦ÂÂ¿Ã¨ÂÂ¡Ã¥ÂÂ Ã¦Â¶Â¨Ã¥ÂÂÃ¦Â¯ÂÃ¯Â¼Â



    lb_ratio = lb / zt if zt > 0 else 0







    # Ã¦ÂÂÃ¦ÂÂ°Ã¨Â´Â¡Ã§ÂÂ®



    idx_pct = index_data.get("change_pct", 0)



    idx_score = min(max((idx_pct + 2) / 4 * 100, 0), 100)







    # Ã§Â»Â¼Ã¥ÂÂÃ¨Â¯ÂÃ¥ÂÂ



    score = ratio * 40 + (1 - blast_rate) * 25 + min(lb_ratio, 1) * 20 + idx_score * 0.15







    # Ã¨Â°ÂÃ¦ÂÂ´



    if zt > 100:



        score = min(score + 10, 100)



    if dt > 50:



        score = max(score - 15, 0)







    score = round(min(max(score, 0), 100))







    # Ã©ÂÂ¶Ã¦Â®ÂµÃ¥ÂÂ¤Ã¦ÂÂ­



    if score >= 80: phase = "Ã¤Â¸Â»Ã¥ÂÂÃ¦ÂµÂªÃ£ÂÂ»Ã¥Â¼ÂºÃ¤Â¸ÂÃ¨ÂÂ´"



    elif score >= 65: phase = "Ã©ÂÂÃ¨ÂÂ¡Ã¥ÂÂÃ¥Â¼ÂºÃ£ÂÂ»Ã¥ÂÂ¯Ã¦ÂÂÃ¤Â½Â"



    elif score >= 50: phase = "Ã¥ÂÂÃ¦Â­Â§Ã¥ÂÂ Ã¥Â¤Â§Ã£ÂÂ»Ã¨Â°Â¨Ã¦ÂÂ"



    elif score >= 35: phase = "Ã©ÂÂÃ¦Â½Â®Ã¥ÂÂÃ¦ÂÂÃ£ÂÂ»Ã¥ÂÂÃ¤Â»Â"



    else: phase = "Ã¥ÂÂ°Ã§ÂÂ¹Ã£ÂÂ»Ã©ÂÂ²Ã¥Â®Â"







    # Ã¤Â»ÂÃ¤Â½ÂÃ¥Â»ÂºÃ¨Â®Â®



    if score >= 80: position = "8-10Ã¦ÂÂ"



    elif score >= 65: position = "5-7Ã¦ÂÂ"



    elif score >= 50: position = "3-4Ã¦ÂÂ"



    elif score >= 35: position = "1-2Ã¦ÂÂ"



    else: position = "Ã§Â©ÂºÃ¤Â»Â"







    # Ã§ÂÂ¸Ã¦ÂÂ¿Ã§ÂÂ



    b_rate = round(blast_rate * 100, 1)







    # Ã¥Â¤Â§Ã©ÂÂ¢Ã¨ÂÂ¡Ã¯Â¼ÂÃ§ÂÂ¸Ã¦ÂÂ¿Ã¨ÂÂ¡Ã¤Â¸Â­Ã¨Â·ÂÃ¥Â¹ÂÃ¥Â¤Â§Ã§ÂÂÃ¯Â¼Â



    big_noodles = 0



    for b in pools["blasted"]:



        if b.get("change_pct", 0) < -5:



            big_noodles += 1







    # Ã¨Â¿ÂÃ¦ÂÂ¿Ã¦ÂÂÃ§ÂºÂ§Ã¦ÂÂÃ¥ÂÂÃ§ÂÂÃ¯Â¼ÂÃ¦ÂÂÃ¨Â¿ÂÃ§Â»Â­Ã¦Â¶Â¨Ã¥ÂÂÃ¦ÂÂ°Ã¦ÂÂ®Ã§ÂÂÃ¯Â¼ÂÃ§ÂÂ2Ã¦ÂÂ¿Ã¤Â»Â¥Ã¤Â¸ÂÃ¦ÂÂÃ§ÂºÂ§Ã¯Â¼Â



    board2_up = 0



    board2_cnt = 0



    for c in pools["continuous"]:



        if c.get("board", 0) >= 2:



            board2_cnt += 1



            if c.get("change_pct", 0) > 9:



                board2_up += 1



    promotion = round(board2_up / board2_cnt * 100, 1) if board2_cnt > 0 else 0







    # Ã¦ÂÂ¨Ã¦ÂÂ¥Ã¨Â¿ÂÃ¦ÂÂ¿Ã¦Â¶Â¨Ã¥Â¹ÂÃ¯Â¼ÂÃ§ÂÂ¨Ã¨Â¿ÂÃ§Â»Â­Ã¦Â¶Â¨Ã¥ÂÂÃ¥ÂÂÃ¨Â¡Â¨Ã§ÂÂÃ¦Â¶Â¨Ã¨Â·ÂÃ¥Â¹ÂÃ¥Â¹Â³Ã¥ÂÂÃ¯Â¼Â



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







# ======================== Ã¨Â¿ÂÃ¦ÂÂ¿Ã¦Â¢Â¯Ã©ÂÂ ========================







def build_ladder(pools):



    """Ã¦ÂÂÃ¦ÂÂ¿Ã©Â«ÂÃ¦ÂÂÃ¥ÂºÂÃ§ÂÂÃ¨Â¿ÂÃ¦ÂÂ¿Ã¦Â¢Â¯Ã©ÂÂ"""



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







# ======================== Ã¦Â¶Â¨Ã¨Â·ÂÃ¥ÂÂÃ¦ÂÂÃ¥ÂÂ ========================







def split_limits(pools):



    up = pools["up"]



    down = pools["down"]



    # Ã§Â®ÂÃ¥ÂÂÃ¥ÂÂÃ§Â±Â»



    up_20cm = sum(1 for s in up if s.get("change_pct", 0) > 19)



    down_20cm = sum(1 for s in down if s.get("change_pct", 0) < -19)



    # Ã¤Â¸Â­Ã¥ÂÂÃ¦Â¶Â¨Ã¥ÂÂÃ¯Â¼ÂÃ¦ÂÂÃ¤ÂºÂ¤Ã©Â¢Â>5Ã¤ÂºÂ¿Ã¯Â¼Â



    up_main = sum(1 for s in up if s.get("amount", 0) > 5)



    # Ã©Â«ÂÃ¤Â½ÂÃ¨ÂÂ¡Ã¨Â·ÂÃ¥ÂÂÃ¯Â¼ÂÃ¨Â¿ÂÃ¦ÂÂ¿Ã¨Â¿ÂÃ§ÂÂÃ¨Â·ÂÃ¥ÂÂÃ¨ÂÂ¡Ã¯Â¼ÂÃ§ÂÂ¨Ã¥ÂÂÃ§Â§Â°Ã¨Â¿ÂÃ¤Â¼Â¼Ã¥ÂÂ¤Ã¦ÂÂ­Ã¯Â¼ÂÃ£ÂÂ



    # Ã¦ÂÂ´Ã¤Â¸Â¥Ã¨Â°Â¨Ã¯Â¼ÂÃ¨Â·ÂÃ¥ÂÂÃ¨ÂÂ¡Ã¤Â¸Â­Ã¥ÂÂÃ¦ÂÂÃ¦ÂÂÃ¨Â¿ÂÃ¨Â¿ÂÃ¦ÂÂ¿Ã§ÂÂ



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







# ======================== Ã¥Â¼ÂÃ¥ÂÂ¨Ã¦Â£ÂÃ¦ÂµÂ ========================







def detect_events(current_pools, events_file):



    """Ã¤Â¸ÂÃ¤Â¸ÂÃ¦Â¬Â¡Ã¦ÂÂ°Ã¦ÂÂ®Ã¥Â¯Â¹Ã¦Â¯ÂÃ¦Â£ÂÃ¦ÂµÂÃ¥Â¼ÂÃ¥ÂÂ¨"""



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







    # Ã¦ÂÂ°Ã§ÂÂ¸Ã¦ÂÂ¿



    new_blast = now_zb - prev_zb



    for s in current_pools["blasted"]:



        if s["code"] in new_blast:



            events.append({"time": now, "type": "blast", "msg": f"{s['name']} Ã§ÂÂ¸Ã¦ÂÂ¿"})







    # Ã¦ÂÂ°Ã¨Â·ÂÃ¥ÂÂ



    new_dt = now_dt - prev.get("dt_codes", set())



    for s in current_pools["down"]:



        if s["code"] in new_dt:



            events.append({"time": now, "type": "limit_down", "msg": f"{s['name']} Ã¨Â·ÂÃ¥ÂÂ"})







    # Ã¤Â¿ÂÃ¥Â­ÂÃ¥Â½ÂÃ¥ÂÂÃ§ÂÂ¶Ã¦ÂÂÃ§ÂÂ¨Ã¤ÂºÂÃ¤Â¸ÂÃ¦Â¬Â¡Ã¥Â¯Â¹Ã¦Â¯Â



    with open(events_file, "w", encoding="utf-8") as f:



        json.dump({



            "up_codes": list(now_up),



            "zb_codes": list(now_zb),



            "dt_codes": list(now_dt),



        }, f, ensure_ascii=False)







    # Ã¥ÂÂÃ¥Â¹Â¶Ã¥ÂÂÃ¥ÂÂ²Ã¤ÂºÂÃ¤Â»Â¶



    try:



        all_events_file = events_file.replace(".json", "_all.json")



        if os.path.exists(all_events_file):



            with open(all_events_file, "r", encoding="utf-8") as f:



                old_events = json.load(f)



            events = old_events[-50:] + events  # Ã¤Â¿ÂÃ§ÂÂÃ¦ÂÂÃ¨Â¿Â50Ã¦ÂÂ¡



    except: pass







    return events[-30:]  # Ã¨Â¿ÂÃ¥ÂÂÃ¦ÂÂÃ¨Â¿Â30Ã¦ÂÂ¡







# ======================== Ã¤Â¸Â»Ã¦ÂµÂÃ§Â¨Â ========================







def main():



    print(f"========== {now_str()} Ã¥Â¼ÂÃ¥Â§ÂÃ©ÂÂÃ©ÂÂ ==========")







    index_data = fetch_index()



    if not index_data:



        print("ERROR: Ã¦ÂÂ Ã¦Â³ÂÃ¨ÂÂ·Ã¥ÂÂÃ¦ÂÂÃ¦ÂÂ°Ã¦ÂÂ°Ã¦ÂÂ®")



        return







    pools = fetch_limit_pools()



    sectors = fetch_sectors()



    north = fetch_north_flow()



    dragon = fetch_dragon_tiger()



    history_emotion = fetch_emotion_history()







    print("[6/8] Ã¦ÂÂÃ§Â»ÂªÃ¨Â¯ÂÃ¥ÂÂ...")



    emotion = calc_emotion(index_data, pools)



    ladder = build_ladder(pools)



    max_board = get_max_board(ladder)



    limit_split = split_limits(pools)







    print("[7/8] Ã¥Â¼ÂÃ¥ÂÂ¨Ã¦Â£ÂÃ¦ÂµÂ...")



    events = detect_events(pools, os.path.join(BASE, "events_snapshot.json"))







    # Ã¦ÂÂÃ¥Â»ÂºÃ¨Â¾ÂÃ¥ÂÂº



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







    print("[8/8] Ã¤Â¿ÂÃ¥Â­Â...")



    with open(DASHBOARD_FILE, "w", encoding="utf-8") as f:



        json.dump(dashboard, f, ensure_ascii=False, indent=2)



    print(f"  Ã¢ÂÂ {DASHBOARD_FILE}")







    # Ã¦ÂÂ¶Ã§ÂÂÃ¥ÂÂÃ¨Â¿Â½Ã¥ÂÂ Ã¥ÂÂ°Ã¥ÂÂÃ¥ÂÂ²



    now = datetime.now().time()



    if now >= time(15, 5):



        print("  Ã¦ÂÂ¶Ã§ÂÂÃ¦Â¨Â¡Ã¥Â¼ÂÃ¯Â¼ÂÃ¨Â¿Â½Ã¥ÂÂ Ã¥ÂÂÃ¥ÂÂ²...")



        history = []



        if os.path.exists(HISTORY_FILE):



            with open(HISTORY_FILE, "r", encoding="utf-8") as f:



                history = json.load(f)



        # Ã¥ÂÂ»Ã©ÂÂ



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



        print(f"  Ã¢ÂÂ {HISTORY_FILE} ({len(history)} days)")







    # Ã¦Â±ÂÃ¦ÂÂ»



    e = emotion



    print(f"\n========== Ã©ÂÂÃ©ÂÂÃ¥Â®ÂÃ¦ÂÂ ==========")



    print(f"  Ã¦ÂÂÃ¦ÂÂ°: {index_data['price']:.2f} ({index_data['change_pct']:+.2f}%)")



    print(f"  Ã¦ÂÂÃ§Â»Âª: {e['score']}Ã¥ÂÂ [{e['phase']}] Ã¥Â»ÂºÃ¨Â®Â®: {e['position']}")



    print(f"  Ã¦Â¶Â¨Ã¥ÂÂ: {e['detail']['zt_count']} | Ã¨Â·ÂÃ¥ÂÂ: {e['detail']['dt_count']} | Ã§ÂÂ¸Ã¦ÂÂ¿: {e['detail']['zb_count']}")



    print(f"  Ã§ÂÂ¸Ã¦ÂÂ¿Ã§ÂÂ: {e['detail']['blast_rate']}% | Ã¦ÂÂÃ§ÂºÂ§Ã§ÂÂ: {e['detail']['promotion_rate']}%")



    print(f"  Ã¦ÂÂÃ©Â«ÂÃ¦ÂÂ¿: {max_board}Ã¦ÂÂ¿ | Ã¥Â¤Â§Ã©ÂÂ¢Ã¨ÂÂ¡: {e['detail']['noodle_count']}Ã¥ÂÂª")



    print(f"  Ã¥ÂÂÃ¥ÂÂ: {north:+.2f}Ã¤ÂºÂ¿")







if __name__ == "__main__":



    main()





