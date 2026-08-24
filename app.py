import datetime
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st
import yfinance as yf

# -----------------------------------------------------------------------------
# 1. 頁面基礎設定
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="☯️ 易經 × 亞當理論 × 法人籌碼 × ML量化旗艦儀表板",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# -----------------------------------------------------------------------------
# 2. 基礎資料庫
# -----------------------------------------------------------------------------
GAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
ZHI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
ZHI_ELEMENTS = {
    "子": "水", "亥": "水", "寅": "木", "卯": "木",
    "巳": "火", "午": "火", "申": "金", "酉": "金",
    "辰": "土", "戌": "土", "丑": "土", "未": "土"
}

BAGUA = {
    1: {"name": "乾", "symbol": "☰", "element": "金", "num": 1},
    2: {"name": "兌", "symbol": "☱", "element": "金", "num": 2},
    3: {"name": "離", "symbol": "☲", "element": "火", "num": 3},
    4: {"name": "震", "symbol": "☳", "element": "木", "num": 4},
    5: {"name": "巽", "symbol": "☴", "element": "木", "num": 5},
    6: {"name": "坎", "symbol": "☵", "element": "水", "num": 6},
    7: {"name": "艮", "symbol": "☶", "element": "土", "num": 7},
    0: {"name": "坤", "symbol": "☷", "element": "土", "num": 8},
}

GUA_LINES = {
    1: [True, True, True], 2: [True, True, False], 3: [True, False, True],
    4: [True, False, False], 5: [False, True, True], 6: [False, True, False],
    7: [False, False, True], 0: [False, False, False],
}

SEASON_ELEMENT_MAP = {
    1: "水", 2: "木", 3: "木", 4: "土", 5: "火", 6: "火",
    7: "土", 8: "金", 9: "金", 10: "土", 11: "水", 12: "水",
}

ELEMENT_RELATIONS = {
    ("金", "金"): ("比和", "多空拉鋸，平盤或小幅跳空", "⚠️ 平盤震盪", 0.0),
    ("金", "木"): ("體克用", "耗費精力但能獲勝，開高或震盪趨強", "📈 偏多開高", 0.4),
    ("金", "水"): ("體生用", "自身能量洩出，資金不足，易跳空開低", "📉 偏空開低", -0.4),
    ("金", "火"): ("用克體", "受外力壓制，空頭強勁，大機率跳空開低", "🔻 開低承壓", -1.0),
    ("金", "土"): ("用生體", "獲得外部大吉助力，買盤強勁，強勢跳空開高", "🚀 強勢開高", 1.2),

    ("木", "木"): ("比和", "動能相當，多方平盤附近開出", "⚠️ 平盤震盪", 0.0),
    ("木", "火"): ("體生用", "動能過度消耗，開高易走低或直接開低", "📉 偏空開低", -0.4),
    ("木", "土"): ("體克用", "克服賣壓前行，順勢小幅開高", "📈 偏多開高", 0.4),
    ("木", "金"): ("用克體", "遇到強大賣壓，多頭受挫，跳空開低", "🔻 開低承壓", -1.0),
    ("木", "水"): ("用生體", "資金源源不絕，買單湧入，跳空開高", "🚀 強勢開高", 1.2),

    ("水", "水"): ("比和", "量能平平，隨波逐流，平盤附近開出", "⚠️ 平盤震盪", 0.0),
    ("水", "木"): ("體生用", "資金外流，開盤乏力，偏空開低", "📉 偏空開低", -0.4),
    ("水", "火"): ("體克用", "多頭逆勢反攻，有機會偏多開高", "📈 偏多開高", 0.4),
    ("水", "土"): ("用克體", "遭利空擊中，觀望氣氛濃，跳空開低", "🔻 開低承壓", -1.0),
    ("水", "金"): ("用生體", "水到渠成，買單積極，強勢跳空開高", "🚀 強勢開高", 1.2),

    ("火", "火"): ("比和", "熱度高但多空分歧，高開低走震盪大", "⚠️ 高震盪開盤", 0.1),
    ("火", "土"): ("體生用", "追高力道不足，逢高賣壓沉重，易開低", "📉 偏空開低", -0.4),
    ("火", "金"): ("體克用", "衝破賣壓牆，力道強勁，偏多開高", "📈 偏多開高", 0.4),
    ("火", "水"): ("用克體", "冷水灌頂，空頭力道強，防大跌跳空開低", "🔻 開低承壓", -1.0),
    ("火", "木"): ("用生體", "利多頻傳，資金力挺，強勢漲停或跳空大開高", "🚀 強勢開高", 1.2),

    ("土", "土"): ("比和", "底部堅實，波幅極小，平盤開出", "⚠️ 平盤震盪", 0.0),
    ("土", "金"): ("體生用", "漲勁不足，逢高獲利了結賣壓，偏空開低", "📉 偏空開低", -0.4),
    ("土", "水"): ("體克用", "成功吸收籌碼，緩步墊高，小幅開高", "📈 偏多開高", 0.4),
    ("土", "木"): ("用克體", "主力洗盤拋售，支撐脆弱，跳空開低", "🔻 開低承壓", -1.0),
    ("土", "火"): ("用生體", "買盤支撐力道強，有利多頭，強勢開高", "🚀 強勢開高", 1.2),
}

YAO_EXPLANATIONS = {
    1: {"time": "09:00 - 09:30", "phase": "初爻（地基/開盤）", "lucky": "開盤買氣凝聚，根基穩固，早盤具備衝高動能。", "unlucky": "開盤根基不穩，早盤若強行衝高極易缺乏買盤支撐而迅速回吐。"},
    2: {"time": "09:30 - 10:30", "phase": "二爻（宅舍/主力試水）", "lucky": "主力早盤洗盤甩轎成功，回測支撐不破，浮現低點買訊。", "unlucky": "主力早盤賣壓試探破位，提防短線關鍵支撐位失守。"},
    3: {"time": "10:30 - 11:30", "phase": "三爻（多空拉鋸）", "lucky": "多頭盤中抗跌堅韌，消化逢高賣壓後蓄勢再發。", "unlucky": "多空激戰陷劣勢，盤中洗盤劇烈，全日易收十字線或上影線。"},
    4: {"time": "11:30 - 12:30", "phase": "四爻（突破與轉折）", "lucky": "午盤籌碼沉澱完成，多頭準備向高點發動突破。", "unlucky": "中場走勢出現轉折向下，籌碼鬆動，需防午盤棄守。"},
    5: {"time": "12:30 - 13:00", "phase": "五爻（君位/主力發力）", "lucky": "主力資金發力拉升，午盤易發動強勢突破攻勢！", "unlucky": "提防主力逢高出貨，午盤易出現跳水段殺盤！"},
    6: {"time": "13:00 - 13:30", "phase": "上爻（終局/尾盤作收）", "lucky": "尾盤買氣強烈發酵，易急拉收全日相對高點。", "unlucky": "尾盤賣壓湧現定調，易急跌作收收在相對低檔。"}
}

# -----------------------------------------------------------------------------
# 3. 外資與投信籌碼抓取 API 模組
# -----------------------------------------------------------------------------
@st.cache_data(ttl=3600)
def fetch_chip_data(stock_code: str, start_date_str: str):
    """自 FinMind 取得外資與投信買賣超數據 (張數)"""
    url = "https://api.finmindtrade.com/api/v4/data"
    parameter = {
        "dataset": "TaiwanStockInstitutionalInvestorsBuySell",
        "data_id": stock_code,
        "start_date": start_date_str,
    }
    try:
        r = requests.get(url, params=parameter, timeout=8)
        data = r.json()
        if data.get("msg") == "success" and data.get("data"):
            df_chip = pd.DataFrame(data["data"])
            df_target = df_chip[df_chip["name"].isin(["Foreign_Investor", "Investment_Trust"])]
            if not df_target.empty:
                df_pivot = df_target.pivot_table(
                    index="date", columns="name", values="buy", aggfunc="sum"
                ).fillna(0) - df_target.pivot_table(
                    index="date", columns="name", values="sell", aggfunc="sum"
                ).fillna(0)
                
                for col in ["Foreign_Investor", "Investment_Trust"]:
                    if col not in df_pivot.columns:
                        df_pivot[col] = 0.0
                return df_pivot
    except Exception:
        pass
    return pd.DataFrame()

# -----------------------------------------------------------------------------
# 4. 量化指標與天干地支演算法
# -----------------------------------------------------------------------------
def get_ganzhi_date(date_obj):
    base_date = datetime.date(1900, 1, 31)
    diff_days = (date_obj - base_date).days
    gan_idx = (6 + diff_days) % 10
    zhi_idx = (0 + diff_days) % 12
    zhi_name = ZHI[zhi_idx]
    return f"{GAN[gan_idx]}{zhi_name}日", ZHI_ELEMENTS[zhi_name]

def lines_to_gua_val(lines):
    for val, l in GUA_LINES.items():
        if l == lines:
            return val
    return 0

def calculate_season_factor(ti_element: str, month: int):
    season_element = SEASON_ELEMENT_MAP.get(month, "土")
    if ti_element == season_element:
        return 1.3, "當旺"
    element_generates = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
    if element_generates.get(season_element) == ti_element:
        return 1.15, "相"
    elif element_generates.get(ti_element) == season_element:
        return 0.85, "休"
    else:
        return 0.7, "囚/死"

def get_changed_hexagram(upper_val, lower_val, moving_yao):
    full_lines = GUA_LINES[lower_val] + GUA_LINES[upper_val]
    idx = moving_yao - 1
    full_lines[idx] = not full_lines[idx]
    new_lower_val = lines_to_gua_val(full_lines[0:3])
    new_upper_val = lines_to_gua_val(full_lines[3:6])
    return BAGUA[new_upper_val], BAGUA[new_lower_val]

def calculate_raw_hexagram(stock_code: str, date_obj: datetime.date, prev_close: float, atr_val: float):
    digits = "".join(filter(str.isdigit, stock_code))
    stock_num = int(digits) if digits else 100
    year, month, day = date_obj.year, date_obj.month, date_obj.day

    upper_val = (stock_num + year + month + day) % 8
    upper_卦 = BAGUA[upper_val]
    lower_val = (stock_num + day) % 8
    lower_卦 = BAGUA[lower_val]

    yao_val = (stock_num + year + month + day) % 6
    moving_yao = 6 if yao_val == 0 else yao_val

    if moving_yao <= 3:
        ti_卦, yong_卦, ti_pos = upper_卦, lower_卦, "上卦"
    else:
        ti_卦, yong_卦, ti_pos = lower_卦, upper_卦, "下卦"

    open_rel_key = (ti_卦["element"], yong_卦["element"])
    _, _, open_trend, open_base_factor = ELEMENT_RELATIONS.get(open_rel_key, ("平和", "多空平盤附近開出", "⚠️ 平盤震盪", 0.0))
    season_weight, season_desc = calculate_season_factor(ti_卦["element"], month)
    raw_open_change = open_base_factor * season_weight * (atr_val * 0.3)

    changed_upper, changed_lower = get_changed_hexagram(upper_val, lower_val, moving_yao)
    changed_ti = changed_upper if ti_pos == "上卦" else changed_lower
    changed_yong = changed_lower if ti_pos == "上卦" else changed_upper

    close_rel_key = (changed_ti["element"], changed_yong["element"])
    _, _, close_trend, close_base_factor = ELEMENT_RELATIONS.get(close_rel_key, ("平和", "多空交戰，謹慎看待。", "⚠️ 盤整", 0.0))
    yao_factor = 0.8 + (moving_yao * 0.067)
    raw_close_change = close_base_factor * season_weight * yao_factor * (atr_val * 0.8)

    return {
        "raw_open_change": raw_open_change,
        "raw_close_change": raw_close_change,
        "upper": upper_卦, "lower": lower_卦, "moving_yao": moving_yao,
        "changed_upper": changed_upper, "changed_lower": changed_lower,
        "season_desc": season_desc, "open_trend": open_trend, "close_trend": close_trend
    }

def calculate_adx(df: pd.DataFrame, N: int = 14):
    df = df.copy()
    df['H-L'] = df['High'] - df['Low']
    df['H-PC'] = abs(df['High'] - df['Close'].shift(1))
    df['L-PC'] = abs(df['Low'] - df['Close'].shift(1))
    df['TR'] = df[['H-L', 'H-PC', 'L-PC']].max(axis=1)

    df['+DM'] = np.where((df['High'] - df['High'].shift(1)) > (df['Low'].shift(1) - df['Low']), 
                         np.maximum(df['High'] - df['High'].shift(1), 0), 0)
    df['-DM'] = np.where((df['Low'].shift(1) - df['Low']) > (df['High'] - df['High'].shift(1)), 
                         np.maximum(df['Low'].shift(1) - df['Low'], 0), 0)

    tr_s = df['TR'].rolling(N).sum()
    plus_dm_s = df['+DM'].rolling(N).sum()
    minus_dm_s = df['-DM'].rolling(N).sum()

    plus_di = 100 * (plus_dm_s / tr_s)
    minus_di = 100 * (minus_dm_s / tr_s)
    dx = 100 * (abs(plus_di - minus_di) / (plus_di + minus_di))
    adx = dx.rolling(N).mean()
    return adx.iloc[-1] if not adx.empty and not np.isnan(adx.iloc[-1]) else 20.0

def calculate_adam_reflection(df: pd.DataFrame, adam_days: int = 10):
    sub_df = df.iloc[-adam_days:].copy()
    last_price = float(df["Close"].iloc[-1])
    hist_prices = sub_df["Close"].values[::-1]
    adam_projected_prices = 2 * last_price - hist_prices

    last_date = df.index[-1]
    future_dates = []
    curr_d = last_date
    while len(future_dates) < adam_days:
        curr_d += datetime.timedelta(days=1)
        if curr_d.weekday() < 5:
            future_dates.append(curr_d)

    future_df = pd.DataFrame({"Date": future_dates, "Adam_Price": adam_projected_prices}).set_index("Date")
    return adam_projected_prices[0], future_df

# -----------------------------------------------------------------------------
# 5. 核心迴圈：籌碼融合、勝率統計、殘差遞推與綜合算力
# -----------------------------------------------------------------------------
def get_stock_data_and_analysis(stock_code: str, target_date: datetime.date, backtest_days: int = 20, lr: float = 0.3, adam_days: int = 10):
    digits = "".join(filter(str.isdigit, stock_code))
    if not digits:
        return None, "無效的股票代號"

    tickers = [f"{digits}.TW", f"{digits}.TWO"]
    start_date = target_date - datetime.timedelta(days=120)
    df_chip = fetch_chip_data(digits, start_date.strftime("%Y-%m-%d"))

    for ticker in tickers:
        df = yf.download(ticker, start=start_date, end=target_date + datetime.timedelta(days=1), progress=False)
        if not df.empty and len(df) >= backtest_days + 25:
            if isinstance(df.columns, tuple) or hasattr(df.columns, "levels"):
                df.columns = [col[0] for col in df.columns]

            high_low = df["High"] - df["Low"]
            high_cp = (df["High"] - df["Close"].shift(1)).abs()
            low_cp = (df["Low"] - df["Close"].shift(1)).abs()
            tr = high_low.to_frame("hl").join(high_cp.to_frame("hcp")).join(low_cp.to_frame("lcp")).max(axis=1)
            df["ATR"] = tr.rolling(14).mean().fillna(df["Close"] * 0.02)
            df["MA5"] = df["Close"].rolling(5).mean()
            df["MA20"] = df["Close"].rolling(20).mean()

            adx_val = calculate_adx(df)
            adam_next_target, adam_future_df = calculate_adam_reflection(df, adam_days=adam_days)

            recent_high = float(df["High"].iloc[-adam_days:].max())
            recent_low = float(df["Low"].iloc[-adam_days:].min())

            eval_df = df.iloc[-(backtest_days + 1):-1].copy()
            open_bias_adj = 0.0
            close_bias_adj = 0.0
            rolling_logs = []
            dir_hits = 0
            close_errors = []

            for i in range(len(eval_df)):
                curr_date = eval_df.index[i].date()
                prev_close = df["Close"].iloc[df.index.get_loc(eval_df.index[i]) - 1]
                actual_open = eval_df["Open"].iloc[i]
                actual_close = eval_df["Close"].iloc[i]
                atr = eval_df["ATR"].iloc[i]

                raw = calculate_raw_hexagram(stock_code, curr_date, prev_close, atr)
                pred_open_adj = prev_close + raw["raw_open_change"] + open_bias_adj
                pred_close_adj = prev_close + raw["raw_close_change"] + close_bias_adj

                pred_dir = pred_close_adj >= prev_close
                actual_dir = actual_close >= prev_close
                if pred_dir == actual_dir:
                    dir_hits += 1

                close_err = actual_close - pred_close_adj
                open_err = actual_open - pred_open_adj
                close_errors.append(close_err)

                rolling_logs.append({
                    "步數": f"第 {i+1} 天",
                    "日期": curr_date.strftime("%Y-%m-%d"),
                    "套用開盤修正量": open_bias_adj,
                    "當日實際開盤": actual_open,
                    "校正後預測開盤": pred_open_adj,
                    "開盤剩餘誤差": open_err,
                    "套用收盤修正量": close_bias_adj,
                    "當日實際收盤": actual_close,
                    "校正後預測收盤": pred_close_adj,
                    "收盤剩餘誤差": close_err,
                })

                open_bias_adj += open_err * lr
                close_bias_adj += close_err * lr

            accuracy_rate = (dir_hits / len(eval_df)) * 100.0
            rmse_val = np.sqrt(np.mean(np.square(close_errors)))
            bt_df = pd.DataFrame(rolling_logs)

            last_close = float(df["Close"].iloc[-1])
            last_atr = float(df["ATR"].iloc[-1])
            last_ma5 = float(df["MA5"].iloc[-1])
            last_high = float(df["High"].iloc[-1])
            last_low = float(df["Low"].iloc[-1])
            latest_volume = float(df["Volume"].iloc[-1])
            actual_date = df.index[-1].strftime("%Y-%m-%d")

            # 計算當前外資與投信籌碼偏置金額
            foreign_net, trust_net = 0.0, 0.0
            if not df_chip.empty:
                last_date_str = actual_date
                if last_date_str in df_chip.index:
                    foreign_net = float(df_chip.loc[last_date_str, "Foreign_Investor"])
                    trust_net = float(df_chip.loc[last_date_str, "Investment_Trust"])
                else:
                    foreign_net = float(df_chip["Foreign_Investor"].iloc[-1])
                    trust_net = float(df_chip["Investment_Trust"].iloc[-1])

            total_inst_shares = (foreign_net * 0.6) + (trust_net * 0.4)
            volume_shares = latest_volume / 1000.0 if latest_volume > 0 else 1.0
            chip_ratio = np.clip(total_inst_shares / volume_shares, -1.0, 1.0)
            chip_price_adj = chip_ratio * last_atr * 0.5

            return {
                "last_close": last_close, "last_atr": last_atr, "last_ma5": last_ma5,
                "last_high": last_high, "last_low": last_low, "actual_date": actual_date,
                "final_open_bias_adj": open_bias_adj, "final_close_bias_adj": close_bias_adj,
                "adam_next_target": adam_next_target, "adam_future_df": adam_future_df,
                "adx_val": adx_val, "accuracy_rate": accuracy_rate, "rmse_val": rmse_val,
                "recent_high": recent_high, "recent_low": recent_low, "bt_df": bt_df, "df_history": df,
                "foreign_net": foreign_net, "trust_net": trust_net, "chip_price_adj": chip_price_adj
            }, None

    return None, "找不到該股票歷史價格數據"

# -----------------------------------------------------------------------------
# 6. Streamlit 主 UI 介面
# -----------------------------------------------------------------------------
st.title("☯️ 易經 × 亞當理論 × 法人籌碼 × ML量化旗艦儀表板")
st.caption("即時時空氣場 + 外資投信籌碼 + ADX 趨勢權重 + 亞當對稱 + 20日勝率與殘差RMSE驗證")

st.markdown("---")

col_left, col_right = st.columns([1, 2])

with col_left:
    st.subheader("⚙️ 參數設置")
    stock_input = st.text_input("輸入台股代號", value="2330")
    base_date = st.date_input("選擇基準日期", datetime.date.today())
    learning_rate = st.slider("殘差學習率 (Learning Rate)", 0.1, 0.8, 0.3, 0.05)
    adam_window = st.slider("亞當對稱天數", 5, 20, 10, 1)
    target_mode = st.radio("預測目標時段：", ["預測當天盤勢", "預測次日（隔天）盤勢"], horizontal=True)
    run_btn = st.button("🚀 啟動量化終極儀表板", use_container_width=True)

    st.markdown("---")
    st.subheader("⏱️ 盤中時段爻位追蹤器")
    now_time = datetime.datetime.now().time()
    if datetime.time(9, 0) <= now_time <= datetime.time(9, 30):
        current_phase = "1爻【初爻·開盤階段】"
    elif datetime.time(9, 30) < now_time <= datetime.time(10, 30):
        current_phase = "2爻【二爻·主力試水】"
    elif datetime.time(10, 30) < now_time <= datetime.time(11, 30):
        current_phase = "3爻【三爻·多空交戰】"
    elif datetime.time(11, 30) < now_time <= datetime.time(12, 30):
        current_phase = "4爻【四爻·午盤轉折】"
    elif datetime.time(12, 30) < now_time <= datetime.time(13, 0):
        current_phase = "5爻【五爻·主升/降段】"
    elif datetime.time(13, 0) < now_time <= datetime.time(13, 30):
        current_phase = "6爻【上爻·尾盤定調】"
    else:
        current_phase = "☕ 非交易時段 (盤後定盤期)"

    st.info(f"當前時間對應：**{current_phase}**")

with col_right:
    if run_btn:
        calc_date = base_date + datetime.timedelta(days=1) if target_mode == "預測次日（隔天）盤勢" else base_date

        with st.spinner("算力全開：計算五行氣場、三大法人籌碼偏置、ADX動態權重、亞當對稱與回測勝率..."):
            data, err = get_stock_data_and_analysis(stock_input, base_date, backtest_days=20, lr=learning_rate, adam_days=adam_window)

        if err:
            st.error(f"❌ 數據抓取失敗：{err}")
        else:
            prev_close = data["last_close"]
            atr_val = data["last_atr"]
            adx_val = data["adx_val"]
            adam_target = data["adam_next_target"]
            chip_price_adj = data["chip_price_adj"]

            raw_res = calculate_raw_hexagram(stock_input, calc_date, prev_close, atr_val)
            pred_open = prev_close + raw_res["raw_open_change"] + data["final_open_bias_adj"]
            pred_close = prev_close + raw_res["raw_close_change"] + data["final_close_bias_adj"]

            # ADX 動態權重分配 + 籌碼修正額疊加
            if adx_val > 25:
                weight_adam = 0.7
                weight_iching = 0.3
                trend_status = f"🔥 趨勢強勁 (亞當 70% + 易經 30%)"
            else:
                weight_adam = 0.3
                weight_iching = 0.7
                trend_status = f"⚖️ 帶狀盤整 (易經 70% + 亞當 30%)"

            hybrid_target = (pred_close * weight_iching) + (adam_target * weight_adam) + chip_price_adj
            ganzhi_str, day_elem = get_ganzhi_date(calc_date)

            # 方向性防守價邏輯
            is_bullish = hybrid_target >= prev_close
            if is_bullish:
                stop_loss = data["recent_low"]
                stop_loss_label = f"多頭防守停損價(近{adam_window}日低)"
                stop_loss_action = f"跌破 **{stop_loss:.2f} 元**"
            else:
                stop_loss = data["recent_high"]
                stop_loss_label = f"空頭壓力停損價(近{adam_window}日高)"
                stop_loss_action = f"突破 **{stop_loss:.2f} 元**"

            # 核心指標卡片
            k1, k2, k3, k4 = st.columns(4)
            k1.metric("時空綜合目標價", f"{hybrid_target:.2f}元", delta=f"{hybrid_target - prev_close:+.2f}元")
            k2.metric("近20日方向勝率", f"{data['accuracy_rate']:.1f}%")
            k3.metric("遞推殘差 RMSE", f"{data['rmse_val']:.2f}元")
            k4.metric("ADX 趨勢值", f"{adx_val:.1f}")

            st.caption(f"📊 **動態權重狀態**：{trend_status} ｜ 防守位：**{stop_loss_label} = {stop_loss:.2f} 元**")

            # -----------------------------------------------------------------
            # 視覺化 Plotly 圖表
            # -----------------------------------------------------------------
            df_hist = data["df_history"]
            adam_future_df = data["adam_future_df"]
            
            fig = go.Figure()

            fig.add_trace(go.Candlestick(
                x=df_hist.index, open=df_hist["Open"], high=df_hist["High"], 
                low=df_hist["Low"], close=df_hist["Close"], name="K線"
            ))

            fig.add_trace(go.Scatter(x=df_hist.index, y=df_hist["MA5"], line=dict(color="orange", width=1), name="5MA"))
            fig.add_trace(go.Scatter(x=df_hist.index, y=df_hist["MA20"], line=dict(color="#1E90FF", width=1), name="20MA"))

            concat_adam_x = [df_hist.index[-1]] + list(adam_future_df.index)
            concat_adam_y = [prev_close] + list(adam_future_df["Adam_Price"].values)
            fig.add_trace(go.Scatter(
                x=concat_adam_x, y=concat_adam_y, 
                mode="lines",
                line=dict(color="#BA55D3", width=2, dash="dash"), 
                name="亞當軌跡"
            ))

            upper_band = max(pred_close, adam_target) + (atr_val * 0.5)
            lower_band = min(pred_close, adam_target) - (atr_val * 0.5)

            fig.add_hrect(
                y0=lower_band, y1=upper_band, 
                fillcolor="rgba(255, 215, 0, 0.12)",
                line_width=1, line_dash="dot", line_color="rgba(255, 215, 0, 0.5)"
            )

            fig.update_layout(
                margin=dict(l=5, r=5, t=10, b=10),
                height=320,
                xaxis_rangeslider_visible=False,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="center",
                    x=0.5,
                    font=dict(size=10)
                ),
                yaxis=dict(side="right", tickfont=dict(size=10)),
                xaxis=dict(tickfont=dict(size=10))
            )

            st.plotly_chart(fig, use_container_width=True)

            # 頁籤詳細面板
            t1, t2, t3, t4 = st.tabs(["📜 老易師量化決策卡", "🔄 20日勝率與遞推日誌", "☯️ 卦象與法人籌碼", "🛡️ 風險與停損評估"])

            with t1:
                yao_info = YAO_EXPLANATIONS[raw_res["moving_yao"]]
                st.markdown(f"### 🎯 日辰氣場：{ganzhi_str} ({day_elem})")
                st.write(f"- 開盤預估：**{pred_open:.2f} 元** ({raw_res['open_trend']})")
                st.write(f"- 收盤預估：**{pred_close:.2f} 元** ({raw_res['close_trend']})")
                st.write(f"- 籌碼偏置影響：**{chip_price_adj:+.2f} 元**")
                st.markdown("---")
                st.markdown(f"### ⏱️ 當日關鍵動爻轉折：【{yao_info['time']}】 ({yao_info['phase']})")
                st.info(yao_info["lucky"] if is_bullish else yao_info["unlucky"])

            with t2:
                st.markdown(f"**近 20 日預測方向命中率：{data['accuracy_rate']:.1f}%** ｜ **RMSE 殘差標準差：{data['rmse_val']:.2f} 元**")
                st.dataframe(data["bt_df"].style.format("{:.2f}", subset=[
                    "套用開盤修正量", "當日實際開盤", "校正後預測開盤", "開盤剩餘誤差",
                    "套用收盤修正量", "當日實際收盤", "校正後預測收盤", "收盤剩餘誤差"
                ]), height=250)

            with t3:
                cx, cy, cz = st.columns(3)
                cx.metric("【本卦】上卦", f"{raw_res['upper']['symbol']}{raw_res['upper']['name']}")
                cy.metric("【本卦】下卦", f"{raw_res['lower']['symbol']}{raw_res['lower']['name']}")
                cz.metric("動爻", f"第 {raw_res['moving_yao']} 爻")
                
                c1, c2 = st.columns(2)
                c1.metric("外資買賣超 (張)", f"{data['foreign_net']:+,.0f}")
                c2.metric("投信買賣超 (張)", f"{data['trust_net']:+,.0f}")

            with t4:
                st.warning(
                    f"⚠️ **亞當對稱與籌碼失效機制**：當前看{'多' if is_bullish else '空'}。"
                    f"若標的價格{stop_loss_action} ({stop_loss_label})，"
                    f"代表對稱型態、籌碼保護與氣場結構已破位失效，建議進行強制停損或反向觀望。"
                )

st.caption("⚠️ 免責聲明：本儀表板結合玄學易經、三大法人籌碼、亞當對稱鏡射與機器學習殘差修正，僅供學術程式開發與研究討論，不構成任何商業買賣建議。")
