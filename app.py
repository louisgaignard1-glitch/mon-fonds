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
                else:
                    st.write(f"Aucune colonne 'Adj Close' ou 'Close' trouvée pour {t}")
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
if not weights.empty:
    weights = weights / weights.sum()  # Normaliser les poids pour qu'ils totalisent 1
else:
    st.error("Aucun ticker valide n'a pu être téléchargé.")
    st.stop()

returns = prices.pct_change().fillna(0)
portfolio_returns = (returns * weights).sum(axis=1)
portfolio_index = (1 + portfolio_returns).cumprod()

# =====================
# Benchmark
# =====================
@st.cache_data(ttl=3600)
def load_benchmark(start):
    try:
        b = yf.download(benchmark, start=start)
        if not b.empty:
            if "Adj Close" in b.columns:
                return (1 + b["Adj Close"].pct_change().fillna(0)).cumprod()
            elif "Close" in b.columns:
                return (1 + b["Close"].pct_change().fillna(0)).cumprod()
            else:
                st.error(f"Aucune colonne 'Adj Close' ou 'Close' trouvée pour le benchmark {benchmark}.")
                return pd.Series()
        else:
            st.error(f"Aucune donnée téléchargée pour le benchmark {benchmark}.")
            return pd.Series()
    except Exception as e:
        st.error(f"Erreur lors du téléchargement des données pour le benchmark: {e}")
        return pd.Series()

bench_index = load_benchmark(start)

if bench_index.empty or not isinstance(bench_index, pd.Series):
    st.warning("Aucune donnée de benchmark valide n'a pu être téléchargée. Utilisation d'un benchmark fictif pour la démonstration.")
    # Créer un benchmark fictif pour la démonstration
    bench_index = pd.Series(np.cumprod(1 + np.random.normal(0.0005, 0.02, len(portfolio_index))), index=portfolio_index.index)

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

# Vérification de la performance du portefeuille
portfolio_perf = (portfolio_index.iloc[-1] - 1) * 100 if not portfolio_index.empty else 0
col1.metric("Perf portefeuille", f"{portfolio_perf:.2f}%")

# Vérification de la performance du benchmark
if isinstance(bench_index, pd.Series) and not bench_index.empty:
    bench_perf = (bench_index.iloc[-1] - 1) * 100
else:
    bench_perf = 0
col2.metric("Perf CAC40", f"{bench_perf:.2f}%")

st.caption("Mise à jour automatique toutes les heures")
