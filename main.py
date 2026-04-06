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
st.title("📊 Financial Dashboard (Flexible)")

# =========================
# 📅 DATE SELECTION
# =========================
st.sidebar.header("📅 Select Date Range")

start_date = st.sidebar.date_input("Start Date", date(2023, 1, 1))
end_date = st.sidebar.date_input("End Date", date.today())

# =========================
# 🔍 CUSTOM STOCK INPUT
# =========================
st.sidebar.header("🔍 Search Stocks")

custom_tickers = st.sidebar.text_input(
    "Enter Tickers (comma-separated)",
    "RELIANCE.NS, TCS.NS"
)

custom_list = [t.strip() for t in custom_tickers.split(",") if t.strip()]

# 📌 Default Textile Peers
peers = {
    "VTL.NS": "Vardhman Textiles",
    "ARVIND.NS": "Arvind Ltd",
    "PAGEIND.NS": "Page Industries",
    "WELSPUNLIV.NS": "Welspun Living",
    "KPRMILL.NS": "KPR Mill"
}

# =========================
# 📥 EXCEL FUNCTION
# =========================
def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

# =========================
# 🔥 COMPARABLES (TEXTILE)
# =========================
comp_data = []

for ticker, name in peers.items():
    try:
        data = yf.download(ticker, start=start_date, end=end_date)

        if data.empty:
            continue

        close_prices = data['Close']
        if isinstance(close_prices, pd.DataFrame):
            close_prices = close_prices.iloc[:, 0]

        price = float(close_prices.iloc[-1])
        returns = (close_prices.iloc[-1] / close_prices.iloc[0]) - 1
        volatility = close_prices.pct_change().std()

        comp_data.append({
            "Company": name,
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
# 📊 TAB 1: MARKET (CUSTOM STOCKS)
# =========================
with tab1:
    st.header("Market Overview (Custom Stocks)")

    for stock in custom_list:
        st.subheader(stock)

        data = yf.download(stock, start=start_date, end=end_date)

        if data.empty:
            st.warning(f"No data for {stock}")
            continue

        data = data.reset_index()

        close_prices = data['Close']
        if isinstance(close_prices, pd.DataFrame):
            close_prices = close_prices.iloc[:, 0]

        if len(close_prices) < 2:
            continue

        current_price = float(close_prices.iloc[-1])
        prev_price = float(close_prices.iloc[-2])

        data['MA20'] = close_prices.rolling(20).mean()

        st.metric("Price", round(current_price, 2), round(current_price - prev_price, 2))

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=data['Date'], y=close_prices, name='Price'))
        fig.add_trace(go.Scatter(x=data['Date'], y=data['MA20'], name='MA20'))

        fig.update_layout(template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)

# =========================
# 🏭 TAB 2: COMPARABLES
# =========================
with tab2:
    st.header("Textile Comparable Companies")

    if not comp_df.empty:
        st.dataframe(comp_df)

        excel_data = to_excel(comp_df)

        st.download_button(
            "📥 Download Comparables",
            data=excel_data,
            file_name="comparables.xlsx"
        )
    else:
        st.warning("No comparables data")

# =========================
# 💰 TAB 3: VALUATION
# =========================
with tab3:
    st.header("Valuation")

    client_ebitda = st.number_input("Client EBITDA", value=80000000)

    if not comp_df.empty:
        avg_return = comp_df["Return (%)"].mean()
        avg_volatility = comp_df["Volatility"].mean()

        valuation = client_ebitda * (1 + avg_return/100) * 8

        st.metric("Estimated Value", round(valuation, 2))

        # Recommendation
        st.markdown("---")
        if avg_return > 15:
            st.success("Raise funds now")
        elif avg_return < 0:
            st.warning("Delay fundraising")
        else:
            st.info("Neutral conditions")

# =========================
# 📈 TAB 4: INDUSTRY
# =========================
with tab4:
    st.header("Industry Performance")

    fig = go.Figure()

    for ticker in peers.keys():
        data = yf.download(ticker, start=start_date, end=end_date)

        if not data.empty:
            close_prices = data['Close']
            if isinstance(close_prices, pd.DataFrame):
                close_prices = close_prices.iloc[:, 0]

            normalized = close_prices / close_prices.iloc[0] * 100

            fig.add_trace(go.Scatter(x=data.index, y=normalized, name=ticker))

    st.plotly_chart(fig, use_container_width=True)

# =========================
# ⚠️ TAB 5: RISK
# =========================
with tab5:
    st.header("Risk Analysis")

    risk_data = []

    for ticker in peers.keys():
        data = yf.download(ticker, start=start_date, end=end_date)

        if not data.empty:
            close_prices = data['Close']
            if isinstance(close_prices, pd.DataFrame):
                close_prices = close_prices.iloc[:, 0]

            vol = close_prices.pct_change().std()

            risk_data.append({
                "Stock": ticker,
                "Volatility": round(float(vol), 4)
            })

    st.dataframe(pd.DataFrame(risk_data))
