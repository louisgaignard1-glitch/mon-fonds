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
    "ACA.EB": 0.05,  # Remplacement de ACLN.SW
    "UBER": 0.04,
    "BN.PA": 0.05,  # Remplacement de BOI.PA
    "EOAN.DE": 0.05,
    "GOOGL": 0.03,
    "META": 0.02,
    "HWM": 0.03,
    "AMZN": 0.03,
    # Les fonds ne sont pas disponibles sur Yahoo Finance, ils seront ignorés
}

benchmark = "^FCHI"  # CAC40

start = st.sidebar.date_input("Start date", datetime(2020, 1, 1))

# Convertir les clés du dictionnaire en liste pour éviter les problèmes de hash
tickers = list(allocation.keys())

# =====================
# Téléchargement prix
# =====================
@st.cache_data(ttl=3600)
def load_prices(tickers, start):
    prices = pd.DataFrame()

    for t in tickers:
        try:
            tmp = yf.download(t, start=start)
            if not tmp.empty:
                if "Adj Close" in tmp.columns:
                    prices[t] = tmp["Adj Close"]
                elif "Close" in tmp.columns:
                    prices[t] = tmp["Close"]
        except Exception as e:
            st.write(f"Erreur lors du téléchargement des données pour {t}: {e}")

    return prices

prices = load_prices(tickers, start)

if prices.empty:
    st.error("Aucune donnée de prix n'a pu être téléchargée. Vérifiez les tickers ou votre connexion Internet.")
    st.stop()

# =====================
# Construction portefeuille
# =====================
weights = pd.Series(allocation)
weights = weights[weights.index.isin(prices.columns)]  # Filtrer les poids pour ne garder que les tickers disponibles
weights = weights / weights.sum()  # Normaliser les poids pour qu'ils totalisent 1

returns = prices.pct_change().fillna(0)
portfolio_returns = (returns * weights).sum(axis=1)
portfolio_index = (1 + portfolio_returns).cumprod()

# =====================
# Benchmark
# =====================
@st.cache_data(ttl=3600)
def load_benchmark(start):
    try:
        b = yf.download(benchmark, start=start)["Adj Close"]
        return (1 + b.pct_change().fillna(0)).cumprod()
    except Exception as e:
        st.error(f"Erreur lors du téléchargement des données pour le benchmark: {e}")
        return pd.Series()

bench_index = load_benchmark(start)

if bench_index.empty:
    st.error("Aucune donnée de benchmark n'a pu être téléchargée.")
    st.stop()

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
