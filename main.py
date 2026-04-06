import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import date
import io

st.set_page_config(layout="wide")
st.title("📊 Industry Analysis Dashboard")

# =========================
# 📅 DATE INPUT
# =========================
st.sidebar.header("📅 Date Range")

start_date = st.sidebar.date_input("Start Date", date(2023, 1, 1))
end_date = st.sidebar.date_input("End Date", date.today())

if start_date >= end_date:
    st.error("Start date must be before end date")
    st.stop()

# =========================
# 🏭 INDUSTRIES (EXPANDED)
# =========================
industry_map = {
    "Technology": ["AAPL", "MSFT", "GOOGL", "NVDA", "META", "AMD"],
    "Banking": ["HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "AXISBANK.NS"],
    "Energy": ["RELIANCE.NS", "ONGC.NS", "BPCL.NS", "IOC.NS"],
    "FMCG": ["HINDUNILVR.NS", "ITC.NS", "NESTLEIND.NS", "DABUR.NS"],
    "Pharma": ["SUNPHARMA.NS", "DRREDDY.NS", "CIPLA.NS"],
    "Auto": ["TATAMOTORS.NS", "MARUTI.NS", "M&M.NS"],
    "Metals": ["TATASTEEL.NS", "JSWSTEEL.NS", "HINDALCO.NS"]
}

selected_industry = st.sidebar.selectbox(
    "Select Industry",
    list(industry_map.keys())
)

available_stocks = industry_map[selected_industry]

selected_stocks = st.sidebar.multiselect(
    "Select Companies",
    available_stocks,
    default=available_stocks[:3]
)

tickers = selected_stocks

# =========================
# 📊 BENCHMARK
# =========================
benchmark = "^NSEI" if any(".NS" in t for t in tickers) else "^GSPC"

bench_data = yf.download(benchmark, start=start_date, end=end_date)

if not bench_data.empty:
    bench_close = bench_data['Close']
    if isinstance(bench_close, pd.DataFrame):
        bench_close = bench_close.iloc[:, 0]
    bench_return = float((bench_close.iloc[-1] / bench_close.iloc[0] - 1) * 100)
else:
    bench_return = 0

# =========================
# 🔥 DATA FETCH
# =========================
data_dict = {}

for ticker in tickers:
    try:
        data = yf.download(ticker, start=start_date, end=end_date)

        if data.empty:
            continue

        close = data['Close']
        if isinstance(close, pd.DataFrame):
            close = close.iloc[:, 0]

        if len(close) < 2:
            continue

        returns = float((close.iloc[-1] / close.iloc[0] - 1) * 100)
        volatility = float(close.pct_change().std())
        ma20 = close.rolling(20).mean().iloc[-1]

        data_dict[ticker] = {
            "prices": close,
            "return": returns,
            "volatility": volatility,
            "ma20": ma20,
            "current": float(close.iloc[-1])
        }

    except:
        continue

# =========================
# 📊 PERFORMANCE TABLE
# =========================
perf_data = []

for ticker, val in data_dict.items():
    momentum = "Bullish" if val["current"] > val["ma20"] else "Weak"

    perf_data.append({
        "Stock": ticker,
        "Return (%)": round(val["return"], 2),
        "Volatility": round(val["volatility"], 4),
        "Momentum": momentum
    })

perf_df = pd.DataFrame(perf_data)

# =========================
# 📊 DISPLAY
# =========================
st.header(f"{selected_industry} Industry Analysis")

if perf_df.empty:
    st.error("No performance data available")
    st.stop()

st.subheader("Performance Summary")
st.dataframe(perf_df)

# =========================
# 📊 METRICS
# =========================
avg_return = float(perf_df["Return (%)"].mean())
median_return = float(perf_df["Return (%)"].median())
dispersion = float(perf_df["Return (%)"].std())
avg_vol = float(perf_df["Volatility"].mean())

col1, col2, col3 = st.columns(3)

col1.metric("Average Return", round(avg_return, 2))
col2.metric("Median Return", round(median_return, 2))
col3.metric("Dispersion", round(dispersion, 2))

st.write(f"Benchmark Return: {round(bench_return,2)}%")

# =========================
# 🏆 TOP & BOTTOM
# =========================
top3 = perf_df.sort_values("Return (%)", ascending=False).head(3)
bottom3 = perf_df.sort_values("Return (%)").head(3)

col1, col2 = st.columns(2)

col1.success(f"🏆 Top Performers:\n{top3}")
col2.error(f"📉 Bottom Performers:\n{bottom3}")

# =========================
# ⚠️ RISK
# =========================
st.subheader("Risk Analysis")
st.write(f"Average Volatility: {round(avg_vol, 4)}")

# =========================
# 🧠 INTERPRETATION (FIXED)
# =========================
st.subheader("📌 Interpretation")

if pd.isna(avg_return) or pd.isna(avg_vol):
    st.warning("Insufficient data for interpretation")

else:
    if avg_return > bench_return + 5:
        if avg_vol < 0.03:
            st.success("🚀 Strong sector: High returns with low risk → Ideal for fundraising")
        else:
            st.info("📈 High growth but volatile → Selective investment")

    elif avg_return > bench_return:
        st.info("👍 Slight outperformance → Moderate opportunity")

    elif avg_return < 0:
        st.warning("📉 Negative trend → Avoid or delay investment")

    else:
        st.info("⚖️ Neutral sector → Balanced outlook")

st.write(f"Avg Return: {round(avg_return,2)}% | Avg Volatility: {round(avg_vol,4)}")

# =========================
# 💰 COMPARABLES
# =========================
def get_comparables(tickers):
    comp_data = []

    for ticker in tickers:
        try:
            info = yf.Ticker(ticker).info

            comp_data.append({
                "Stock": ticker,
                "Market Cap": info.get("marketCap"),
                "P/E": info.get("trailingPE"),
                "Revenue": info.get("totalRevenue"),
                "EBITDA": info.get("ebitda")
            })

        except:
            continue

    return pd.DataFrame(comp_data)

comp_df = get_comparables(tickers)

st.subheader("Comparables")
st.dataframe(comp_df)

# =========================
# 📥 EXCEL EXPORT
# =========================
def generate_excel(perf_df, comp_df):
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        perf_df.to_excel(writer, sheet_name='Performance', index=False)
        comp_df.to_excel(writer, sheet_name='Comparables', index=False)

    return output.getvalue()

excel_data = generate_excel(perf_df, comp_df)

st.download_button(
    "📥 Download Full Report (Excel)",
    data=excel_data,
    file_name="industry_analysis.xlsx"
)
