#!/usr/bin/env python
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
        print(f"  Sector columns: {list(df.columns)}")
        name_col = None
        pct_col = None
        leader_col = None
        leader_pct_col = None
        for c in df.columns:
            if '名称' in str(c) or '板块' in str(c) or 'name' in str(c).lower():
                if name_col is None: name_col = c
            if '涨跌幅' in str(c) or 'pct' in str(c).lower():
                if pct_col is None and '领' not in str(c): pct_col = c
            if '领涨' in str(c) or '龙头' in str(c) or 'leader' in str(c).lower():
                if '涨幅' in str(c) or 'pct' in str(c).lower():
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
                df2 = df2.sort_values('涨跌幅', ascending=False)
                for i, (_, r) in enumerate(df2.iterrows()):
                    item = {
                        "name": str(r['板块名称']),
                        "change_pct": safe_float(r['涨跌幅']),
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
        df = ak.stock_lhb_detail_em()
        if df is not None and not df.empty:
            for _, r in df.head(30).iterrows():
                result.append({
                    "code": str(r.get('代码', '')),
                    "name": str(r.get('名称', '')),
                    "change_pct": safe_float(r.get('涨跌幅', 0)),
