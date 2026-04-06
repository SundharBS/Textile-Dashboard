import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

# 🔄 Auto refresh
st_autorefresh(interval=15000, key="refresh")

st.set_page_config(layout="wide")
st.title("📊 Textile Fundraising Dashboard")

# 📌 Textile Peers
peers = {
    "VTL.NS": "Vardhman Textiles",
    "ARVIND.NS": "Arvind Ltd",
    "PAGEIND.NS": "Page Industries",
    "WELSPUNLIV.NS": "Welspun Living",
    "KPRMILL.NS": "KPR Mill"
}

# 🧩 Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Market",
    "🏭 Comparables",
    "💰 Valuation",
    "📈 Industry",
    "⚠️ Risk"
])

# =========================
# 📊 TAB 1: MARKET
# =========================
with tab1:
    st.header("Market Overview")

    stocks = st.multiselect(
        "Select Stocks",
        list(peers.keys()),
        default=["VTL.NS", "KPRMILL.NS"]
    )

    period = st.selectbox("Time Period", ["1mo", "3mo", "6mo", "1y"])

    portfolio_value = 0

    for stock in stocks:
        st.subheader(stock)

        data = yf.download(stock, period=period)

        if data.empty:
            st.warning(f"No data for {stock}")
            continue

        data = data.reset_index()

        close_prices = data['Close']

        # ✅ FIX multi-index issue
        if isinstance(close_prices, pd.DataFrame):
            close_prices = close_prices.iloc[:, 0]

        # Ensure enough data
        if len(close_prices) < 2:
            st.warning(f"Not enough data for {stock}")
            continue

        # ✅ FIX: convert to float
        current_price = float(close_prices.iloc[-1])
        prev_price = float(close_prices.iloc[-2])

        portfolio_value += current_price

        # Moving Average
        data['MA20'] = close_prices.rolling(20).mean()

        st.metric(
            "Price",
            round(current_price, 2),
            round(current_price - prev_price, 2)
        )

        # Chart
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=data['Date'],
            y=close_prices,
            name='Price'
        ))

        fig.add_trace(go.Scatter(
            x=data['Date'],
            y=data['MA20'],
            name='MA20'
        ))

        fig.update_layout(template="plotly_dark")

        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.metric("Total Portfolio Value", round(portfolio_value, 2))


# =========================
# 🏭 TAB 2: COMPARABLES
# =========================
with tab2:
    st.header("Textile Comparable Companies")

    comp_data = []

    for ticker, name in peers.items():
        try:
            info = yf.Ticker(ticker).info

            comp_data.append({
                "Company": name,
                "Ticker": ticker,
                "P/E": info.get("trailingPE"),
                "Market Cap": info.get("marketCap"),
                "Revenue": info.get("totalRevenue"),
                "EBITDA": info.get("ebitda")
            })
        except:
            continue

    comp_df = pd.DataFrame(comp_data)

    st.dataframe(comp_df)


# =========================
# 💰 TAB 3: VALUATION
# =========================
with tab3:
    st.header("Client Valuation Estimator")

    client_ebitda = st.number_input("Client EBITDA (₹)", value=80000000)

    if not comp_df.empty:
        comp_clean = comp_df.dropna()

        if not comp_clean.empty:
            comp_clean["EV/EBITDA"] = comp_clean["Market Cap"] / comp_clean["EBITDA"]

            avg_multiple = comp_clean["EV/EBITDA"].mean()

            valuation = client_ebitda * avg_multiple

            st.metric("Estimated Valuation (₹)", round(valuation, 2))
            st.write("Average EV/EBITDA:", round(avg_multiple, 2))
        else:
            st.warning("Not enough clean data")
    else:
        st.warning("Comparables data not available")


# =========================
# 📈 TAB 4: INDUSTRY
# =========================
with tab4:
    st.header("Textile Sector Performance")

    fig = go.Figure()

    for ticker in peers.keys():
        data = yf.download(ticker, period="6mo")

        if not data.empty:
            close_prices = data['Close']

            if isinstance(close_prices, pd.DataFrame):
                close_prices = close_prices.iloc[:, 0]

            normalized = close_prices / close_prices.iloc[0] * 100

            fig.add_trace(go.Scatter(
                x=data.index,
                y=normalized,
                name=ticker
            ))

    fig.update_layout(template="plotly_dark")

    st.plotly_chart(fig, use_container_width=True)


# =========================
# ⚠️ TAB 5: RISK
# =========================
with tab5:
    st.header("Risk Analysis (Volatility)")

    risk_data = []

    for ticker in peers.keys():
        data = yf.download(ticker, period="3mo")

        if not data.empty:
            close_prices = data['Close']

            if isinstance(close_prices, pd.DataFrame):
                close_prices = close_prices.iloc[:, 0]

            volatility = close_prices.pct_change().std()

            risk_data.append({
                "Stock": ticker,
                "Volatility": round(float(volatility), 4)
            })

    risk_df = pd.DataFrame(risk_data)

    st.dataframe(risk_df)
