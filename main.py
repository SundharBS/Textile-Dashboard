import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh
import io
from datetime import date

# 🔄 Auto refresh
st_autorefresh(interval=15000, key="refresh")

st.set_page_config(layout="wide")
st.title("📊 Financial Dashboard")

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
# 🔍 STOCK INPUT
# =========================
st.sidebar.header("🔍 Stocks")

stock_input = st.sidebar.text_input(
    "Enter Stocks (comma-separated)",
    "RELIANCE.NS, TCS.NS"
)

stock_list = [s.strip().upper() for s in stock_input.split(",") if s.strip()]

# =========================
# 🏭 PEER INPUT
# =========================
st.sidebar.header("🏭 Peer Group")

peer_input = st.sidebar.text_input(
    "Enter Peer Stocks (comma-separated)",
    "INFY.NS, HDFCBANK.NS"
)

peer_list = [p.strip().upper() for p in peer_input.split(",") if p.strip()]

# =========================
# 📥 EXCEL FUNCTION
# =========================
def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

# =========================
# 🔧 SAFE DOWNLOAD FUNCTION
# =========================
def get_close(data):
    if 'Close' not in data:
        return None

    close = data['Close']
    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]

    return close.dropna()

# =========================
# 🔥 COMPARABLES
# =========================
comp_data = []

for ticker in peer_list:
    try:
        data = yf.download(ticker, start=start_date, end=end_date)

        close_prices = get_close(data)

        if close_prices is None or len(close_prices) < 2:
            continue

        price = float(close_prices.iloc[-1])
        returns = (close_prices.iloc[-1] / close_prices.iloc[0]) - 1
        volatility = close_prices.pct_change().std()

        comp_data.append({
            "Ticker": ticker,
            "Price": round(price, 2),
            "Return (%)": round(returns * 100, 2),
            "Volatility": round(float(volatility), 4)
        })

    except:
        continue

comp_df = pd.DataFrame(comp_data)

# =========================
# 🧩 TABS
# =========================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Market",
    "🏭 Comparables",
    "💰 Valuation",
    "📈 Industry",
    "⚠️ Risk"
])

# =========================
# 📊 MARKET
# =========================
with tab1:
    st.header("Market Overview")

    for stock in stock_list:
        try:
            data = yf.download(stock, start=start_date, end=end_date)
            close_prices = get_close(data)

            if close_prices is None or len(close_prices) < 2:
                st.warning(f"No valid data for {stock}")
                continue

            df = close_prices.reset_index()

            current_price = float(close_prices.iloc[-1])
            prev_price = float(close_prices.iloc[-2])

            df['MA20'] = close_prices.rolling(20).mean().values

            st.subheader(stock)
            st.metric("Price", round(current_price, 2),
                      round(current_price - prev_price, 2))

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df['Date'], y=close_prices, name='Price'))
            fig.add_trace(go.Scatter(x=df['Date'], y=df['MA20'], name='MA20'))

            fig.update_layout(template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)

        except:
            st.warning(f"Error loading {stock}")

# =========================
# 🏭 COMPARABLES
# =========================
with tab2:
    st.header("Peer Comparables")

    if not comp_df.empty:
        st.dataframe(comp_df)

        st.download_button(
            "📥 Download Comparables",
            data=to_excel(comp_df),
            file_name="comparables.xlsx"
        )
    else:
        st.warning("No comparables data")

# =========================
# 💰 VALUATION
# =========================
with tab3:
    st.header("Valuation")

    client_ebitda = st.number_input("Client EBITDA", value=80000000)

    if not comp_df.empty:
        avg_return = comp_df["Return (%)"].mean()
        avg_volatility = comp_df["Volatility"].mean()

        valuation = client_ebitda * (1 + avg_return/100) * 8

        low = valuation * 0.9
        high = valuation * 1.1

        st.metric("Estimated Value", round(valuation, 2))
        st.write(f"Range: ₹{round(low)} - ₹{round(high)}")

        val_df = pd.DataFrame({
            "Metric": ["Value", "Low", "High"],
            "Amount": [valuation, low, high]
        })

        st.download_button(
            "📥 Download Valuation",
            data=to_excel(val_df),
            file_name="valuation.xlsx"
        )

        st.markdown("---")

        if avg_return > 15 and avg_volatility < 0.02:
            st.success("Strong growth → Raise funds")
        elif avg_return < 0:
            st.warning("Negative trend → Delay")
        else:
            st.info("Neutral")

    else:
        st.warning("No comparables available")

# =========================
# 📈 INDUSTRY
# =========================
with tab4:
    st.header("Peer Performance")

    fig = go.Figure()
    valid = False

    for ticker in peer_list:
        try:
            data = yf.download(ticker, start=start_date, end=end_date)
            close_prices = get_close(data)

            if close_prices is None or len(close_prices) < 2:
                continue

            normalized = close_prices / close_prices.iloc[0] * 100

            fig.add_trace(go.Scatter(
                x=close_prices.index,
                y=normalized,
                name=ticker
            ))
            valid = True

        except:
            continue

    if valid:
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No industry data")

# =========================
# ⚠️ RISK
# =========================
with tab5:
    st.header("Risk Analysis")

    risk_data = []

    for ticker in peer_list:
        try:
            data = yf.download(ticker, start=start_date, end=end_date)
            close_prices = get_close(data)

            if close_prices is None or len(close_prices) < 2:
                continue

            vol = close_prices.pct_change().std()

            risk_data.append({
                "Stock": ticker,
                "Volatility": round(float(vol), 4)
            })

        except:
            continue

    risk_df = pd.DataFrame(risk_data)

    if not risk_df.empty:
        st.dataframe(risk_df)
    else:
        st.warning("No risk data")
