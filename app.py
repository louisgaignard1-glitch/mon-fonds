import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="Portfolio vs CAC40", layout="wide")

st.title("📊 Portfolio vs CAC40")

# =====================
# Allocation
# =====================
allocation = {
    "TTE.PA": 0.05,
    "MC.PA": 0.05,
    "INGA.AS": 0.05,
    "SAP.DE": 0.04,
    "ACLN.SW": 0.05,
    "UBER": 0.04,
    "BOI.PA": 0.05,
    "EOAN.DE": 0.05,
    "GOOGL": 0.03,
    "META": 0.02,
    "HWM": 0.03,
    "AMZN": 0.03,
    "LU0912261970": 0.08,
    "LU1331974276": 0.08,
    "FR0007008750": 0.09,
    "LU0292585626": 0.08,
    "FR0010541821": 0.05,
    "FR0011268705": 0.08
}

benchmark = "^FCHI"  # CAC40

start = st.sidebar.date_input("Start date", datetime(2020,1,1))

# =====================
# Téléchargement prix
# =====================
@st.cache_data(ttl=3600)
def load_prices(tickers, start):

    tickers = list(tickers)  # 🔥 fix cache hash

    prices = pd.DataFrame()

    for t in tickers:
        try:
            tmp = yf.download(t, start=start)["Adj Close"]
            prices[t] = tmp
        except:
            pass

    try:
        override = pd.read_csv("prices_override.csv", index_col=0, parse_dates=True)
        prices = prices.combine_first(override)
    except:
        pass

    return prices

# =====================
# Construction portefeuille
# =====================
weights = pd.Series(allocation)

returns = prices.pct_change().fillna(0)
portfolio_returns = (returns * weights).sum(axis=1)
portfolio_index = (1 + portfolio_returns).cumprod()

# =====================
# Benchmark
# =====================
@st.cache_data(ttl=3600)
def load_benchmark(start):
    b = yf.download(benchmark, start=start)["Adj Close"]
    return (1 + b.pct_change().fillna(0)).cumprod()

bench_index = load_benchmark(start)

# =====================
# Graphique
# =====================
fig = go.Figure()

fig.add_trace(go.Scatter(
    x=portfolio_index.index,
    y=portfolio_index,
    name="Portfolio",
    line=dict(width=3)
))

fig.add_trace(go.Scatter(
    x=bench_index.index,
    y=bench_index,
    name="CAC40",
    line=dict(width=3)
))

fig.update_layout(
    height=600,
    template="plotly_white",
    title="Performance cumulée"
)

st.plotly_chart(fig, use_container_width=True)

# =====================
# Metrics
# =====================
st.subheader("📈 Statistiques")

col1, col2 = st.columns(2)

col1.metric("Perf portefeuille", f"{(portfolio_index.iloc[-1]-1)*100:.2f}%")
col2.metric("Perf CAC40", f"{(bench_index.iloc[-1]-1)*100:.2f}%")

st.caption("Mise à jour automatique toutes les heures")
