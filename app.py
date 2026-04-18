import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta

st.set_page_config(page_title="Portfolio vs Benchmark", layout="wide")
st.title("📊 Portfolio vs Benchmark composite")

# =====================
# Allocation portefeuille
# =====================
allocation = {
    "TTE.PA": 0.05,
    "MC.PA": 0.05,
    "INGA.AS": 0.05,
    "SAP.DE": 0.04,
    "ACLN.SW": 0.05,
    "THEON.AS": 0.04,
    "BOI.PA": 0.05,
    "EOAN.DE": 0.05,
    "GOOGL": 0.03,
    "META": 0.02,
    "HWM": 0.03,
    "AMZN": 0.03,
    "0P0000ZWX4.F": 0.08,
    "0P0001861S.F": 0.08,
    "0P00000M6C.F": 0.09,
    "0P00008ESK.F": 0.08,
    "0P0000A6ZG.F": 0.05,
    "0P0000WHLW.F": 0.08
}

tickers = list(allocation.keys())
start = st.sidebar.date_input("Start date", datetime(2020, 1, 1))

# =====================
# Chargement des prix (avec solutions de repli)
# =====================
@st.cache_data(ttl=3600)
def download_single_ticker(ticker, start, max_retries=3):
    """Télécharge un ticker avec plusieurs tentatives et solutions de repli."""
    if ticker == "TTE.PA":
        # Tentatives spécifiques pour TTE.PA
        for attempt in range(max_retries):
            try:
                tmp = yf.download(ticker, start=start, auto_adjust=False, progress=False)
                if not tmp.empty:
                    return tmp
            except:
                pass

            try:
                ticker_obj = yf.Ticker(ticker)
                tmp = ticker_obj.history(start=start)
                if not tmp.empty:
                    return tmp
            except:
                pass

            try:
                # Solution de repli : utiliser FP.PA (TotalEnergies)
                tmp = yf.download("FP.PA", start=start, auto_adjust=False, progress=False)
                if not tmp.empty:
                    return tmp
            except:
                pass

    else:
        # Tentatives standard pour les autres tickers
        for attempt in range(max_retries):
            try:
                tmp = yf.download(ticker, start=start, auto_adjust=False, progress=False)
                if not tmp.empty:
                    return tmp
            except:
                pass

            try:
                ticker_obj = yf.Ticker(ticker)
                tmp = ticker_obj.history(start=start)
                if not tmp.empty:
                    return tmp
            except:
                pass

    # Si tout échoue, retourner un DataFrame vide
    return pd.DataFrame()

@st.cache_data(ttl=3600)
def load_prices(tickers, start):
    prices = pd.DataFrame()
    failed_tickers = []

    for t in tickers:
        tmp = download_single_ticker(t, start)
        if tmp.empty:
            failed_tickers.append(t)
            # Créer une série vide pour l'actif manquant (remplie plus tard)
            prices[t] = np.nan
        else:
            if isinstance(tmp.columns, pd.MultiIndex):
                tmp.columns = tmp.columns.get_level_values(0)
            if "Adj Close" in tmp.columns:
                prices[t] = tmp["Adj Close"]
            elif "Close" in tmp.columns:
                prices[t] = tmp["Close"]

    # Remplir les valeurs manquantes avec la dernière valeur disponible (forward fill)
    prices = prices.ffill()

    if not failed_tickers:
        st.success("Tous les actifs ont été téléchargés avec succès !")
    else:
        st.warning(f"Les tickers suivants n'ont pas pu être téléchargés : {', '.join(failed_tickers)}. Leurs poids seront conservés, mais leurs performances seront nulles.")

    return prices, failed_tickers

prices, failed_tickers = load_prices(tickers, start)
if prices.empty:
    st.error("Aucune donnée de prix n'a pu être téléchargée.")
    st.stop()

# =====================
# Construction portefeuille (sans renormalisation)
# =====================
weights = pd.Series(allocation)  # Poids effectifs = poids cibles

# Afficher les actifs manquants
if failed_tickers:
    missing_pct = sum(allocation[t] for t in failed_tickers) * 100
    st.warning(
        f"⚠️ **{len(failed_tickers)} actif(s) non téléchargé(s)** (représentant {missing_pct:.1f}% de l'allocation) :\n"
        + "\n".join([f"- `{t}` ({allocation[t]*100:.1f}%)" for t in failed_tickers])
    )

# =====================
# Tableau de contrôle des poids
# =====================
with st.expander("🔍 Vérification des poids effectifs du portefeuille"):
    ticker_names_display = {
        "TTE.PA": "TotalEnergies", "MC.PA": "LVMH", "INGA.AS": "ING Groep",
        "SAP.DE": "SAP", "ACLN.SW": "ACLN", "THEON.AS": "Theon Intl",
        "BOI.PA": "Boiron", "EOAN.DE": "E.ON", "GOOGL": "Alphabet",
        "META": "Meta", "HWM": "Howmet", "AMZN": "Amazon",
        "0P0000ZWX4.F": "Helium Fund Perf A EUR",
        "0P0001861S.F": "Eleva Abs Ret Eurp S EUR",
        "0P00000M6C.F": "R-co Conviction Credit Euro",
        "0P00008ESK.F": "AXAIMFIIS US Short Dur HY",
        "0P0000A6ZG.F": "Immobilier 21 AC",
        "0P0000WHLW.F": "GemEquity R",
    }

    df_weights = pd.DataFrame({
        "Actif": [ticker_names_display.get(t, t) for t in weights.index],
        "Ticker": weights.index,
        "Poids cible": [f"{weights[t]*100:.1f}%" for t in weights.index],
        "Statut": ["✅ Disponible" if t not in failed_tickers else "❌ Non téléchargé" for t in weights.index],
    }).reset_index(drop=True)

    st.dataframe(df_weights, use_container_width=True)
    total_effectif = weights.sum() * 100
    st.caption(f"Total poids effectif : {total_effectif:.1f}% (identique aux poids cibles)")

# =====================
# Télécharger EUR/USD
# =====================
fx = yf.download("EURUSD=X", start=start, auto_adjust=False, progress=False)
if fx.empty:
    st.error("Impossible de télécharger les données EUR/USD.")
    st.stop()
if isinstance(fx.columns, pd.MultiIndex):
    fx.columns = fx.columns.get_level_values(0)
if "Adj Close" in fx.columns:
    fx_series = fx["Adj Close"]
elif "Close" in fx.columns:
    fx_series = fx["Close"]
else:
    fx_series = fx.iloc[:, 0]
fx_series.index = pd.to_datetime(fx_series.index)

# =====================
# NAV portefeuille non hedgé
# =====================
prices_eur = prices.copy()

# Conversion des actifs en USD en EUR
usd_tickers = ["GOOGL", "META", "HWM", "AMZN"]
for t in usd_tickers:
    if t in prices.columns and t not in failed_tickers:
        combined = pd.concat([prices[t], fx_series], axis=1, join='inner').ffill()
        if len(combined.columns) == 2:
            combined.columns = ['price', 'fx']
            prices_eur[t] = combined['price'] * (1 / combined['fx'])

# Remplir les valeurs manquantes avec la dernière valeur disponible
prices_eur = prices_eur.ffill()

# Calculer les rendements (0% pour les actifs manquants)
returns = prices_eur.pct_change().fillna(0)
portfolio_returns = (returns * weights).sum(axis=1)
portfolio_index = (1 + portfolio_returns).cumprod()

# =====================
# NAV portefeuille hedgé
# =====================
hedged_prices = prices.copy()
for t in usd_tickers:
    if t in prices.columns and t not in failed_tickers:
        combined = pd.concat([prices[t], fx_series], axis=1, join='outer').ffill()
        if len(combined.columns) == 2:
            combined.columns = ['price', 'fx']
            hedged_prices[t] = combined['price']

hedged_prices = hedged_prices.ffill()
hedged_returns = hedged_prices.pct_change().fillna(0)
portfolio_returns_hedged = (hedged_returns * weights).sum(axis=1)
portfolio_index_hedged = (1 + portfolio_returns_hedged).cumprod()

# =====================
# Benchmark composite
# =====================
@st.cache_data(ttl=3600)
def load_benchmark_composite(start):
    benchmark_weights = {
        "IEV": 0.35, "SPY": 0.20, "TLT": 0.25, "VNQ": 0.10, "EEM": 0.05
    }
    prices = pd.DataFrame()
    for ticker in benchmark_weights.keys():
        tmp = yf.download(ticker, start=start, auto_adjust=False, progress=False)
        if not tmp.empty:
            if isinstance(tmp.columns, pd.MultiIndex):
                tmp.columns = tmp.columns.get_level_values(0)
            if "Adj Close" in tmp.columns:
                prices[ticker] = tmp["Adj Close"]
            elif "Close" in tmp.columns:
                prices[ticker] = tmp["Close"]
    if prices.empty:
        st.error("Aucune donnée de benchmark n'a pu être téléchargée.")
        st.stop()
    prices = prices.ffill()
    weights = pd.Series(benchmark_weights)
    returns = prices.pct_change().fillna(0)
    bench_returns = (returns * weights).sum(axis=1)
    return (1 + bench_returns).cumprod()

bench_index = load_benchmark_composite(start)
if bench_index.empty:
    st.error("Impossible de calculer le benchmark.")
    st.stop()

common_index = portfolio_index.index.intersection(bench_index.index)
portfolio_index = portfolio_index.loc[common_index]
portfolio_index_hedged = portfolio_index_hedged.loc[common_index]
bench_index = bench_index.loc[common_index]

# =====================
# Graphique principal
# =====================
fig = go.Figure()
fig.add_trace(go.Scatter(x=portfolio_index.index, y=portfolio_index, name="Portfolio", line=dict(width=3, color='blue')))
fig.add_trace(go.Scatter(x=bench_index.index, y=bench_index, name="Benchmark composite", line=dict(width=3, color='red')))
fig.add_trace(go.Scatter(x=portfolio_index_hedged.index, y=portfolio_index_hedged, name="Portfolio hedgé USD", line=dict(width=3, dash="dot", color="green")))
fig.update_layout(height=600, template="plotly_white", title="Performance cumulée")
st.plotly_chart(fig, use_container_width=True)

# =====================
# Les 5 lignes les plus performantes sur le dernier mois
# =====================
st.subheader("🏆 Les 5 lignes les plus performantes sur le dernier mois")

ticker_names = {
    "TTE.PA": "TotalEnergies", "MC.PA": "LVMH", "INGA.AS": "ING Group",
    "SAP.DE": "SAP", "ACLN.SW": "ACLN", "THEON.AS": "Theon Intl",
    "BOI.PA": "Boiron", "EOAN.DE": "E.ON", "GOOGL": "Alphabet",
    "META": "Meta", "HWM": "Howmet", "AMZN": "Amazon",
    "0P0000ZWX4.F": "Helium Fund Perf A EUR",
    "0P0001861S.F": "Eleva Abs Ret Eurp S EUR",
    "0P00000M6C.F": "R-co Conviction Credit Euro",
    "0P00008ESK.F": "AXAIMFIIS US SD HY EUR H",
    "0P0000A6ZG.F": "Immobilier 21 AC",
    "0P0000WHLW.F": "GemEquity R",
}

# Filtrer les 30 derniers jours calendaires
month_start = prices_eur.index[-1] - timedelta(days=30)
prices_month = prices_eur[prices_eur.index >= month_start].ffill()

if len(prices_month) >= 2:
    # Performance de chaque ligne sur le mois (0% pour les actifs manquants)
    monthly_perf = {}
    for t in prices_month.columns:
        if t in failed_tickers:
            monthly_perf[t] = 0.0  # Performance nulle pour les actifs manquants
        else:
            monthly_perf[t] = (prices_month[t].iloc[-1] / prices_month[t].iloc[0] - 1) * 100

    monthly_perf = pd.Series(monthly_perf).sort_values(ascending=False)
    top5 = monthly_perf.head(5)

    col_bar, col_line = st.columns(2)
    top5_labels = [ticker_names.get(t, t) for t in top5.index]

    # --- Graphique barres ---
    with col_bar:
        colors = ['#2ecc71' if v >= 0 else '#e74c3c' for v in top5.values]
        fig_bar = go.Figure(go.Bar(
            x=top5_labels,
            y=top5.values,
            marker_color=colors,
            text=[f"{v:.2f}%" for v in top5.values],
            textposition='outside'
        ))
        fig_bar.update_layout(
            title="Performance mensuelle (%)",
            template="plotly_white",
            yaxis_title="%",
            height=400,
            showlegend=False
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    # --- Graphique lignes ---
    with col_line:
        fig_line = go.Figure()
        for ticker in top5.index:
            if ticker in prices_month.columns:
                series = prices_month[ticker]
                if len(series) >= 2:
                    normalized = (series / series.iloc[0]) * 100
                    fig_line.add_trace(go.Scatter(
                        x=normalized.index,
                        y=normalized,
                        name=ticker_names.get(ticker, ticker),
                        mode='lines',
                        line=dict(width=2)
                    ))
        fig_line.update_layout(
            title="Évolution normalisée sur le mois (base 100)",
            template="plotly_white",
            yaxis_title="Base 100",
            height=400
        )
        st.plotly_chart(fig_line, use_container_width=True)

    # Tableau récapitulatif
    st.markdown("**Détail du Top 5**")
    df_top5 = pd.DataFrame({
        "Actif": top5_labels,
        "Ticker": top5.index,
        "Performance mois": [f"{v:.2f}%" for v in top5.values],
        "Poids dans le portefeuille": [f"{weights[t]*100:.1f}%" for t in top5.index],
        "Statut": ["✅ Disponible" if t not in failed_tickers else "❌ Non téléchargé" for t in top5.index]
    }).reset_index(drop=True)
    st.dataframe(df_top5, use_container_width=True)
else:
    st.warning("Pas assez de données disponibles pour calculer le top 5 mensuel.")

# =====================
# Texte explicatif
# =====================
st.subheader("📊 Composition du benchmark")
st.markdown("""
Le benchmark composite reflète la structure multi-actifs du portefeuille :
• 35% MSCI Europe Index (IEV) → actions européennes
• 20% S&P 500 → actions américaines
• 25% Obligations américaines à long terme → obligations
• 10% Immobilier américain → immobilier
• 5% MSCI Emerging Markets → actions émergentes
""")

st.subheader("💱 Couverture FX USD")
st.markdown("""
Cette simulation couvre le risque de change des actions américaines en utilisant un **contrat forward** pour figer le taux EUR/USD.
**Formule appliquée :**
Return hedgé = Return en USD − Variation du taux EUR/USD
→ Cela neutralise l'impact des fluctuations du change.
*(Simplification : pas de coût de couverture inclus.)*
""")

# =====================
# Calcul des performances
# =====================
def calculate_performance(index_series, days):
    if len(index_series) < 2:
        return 0.0
    start_date = index_series.index[-1] - timedelta(days=days)
    if start_date < index_series.index[0]:
        start_date = index_series.index[0]
    start_value = index_series[index_series.index >= start_date].iloc[0]
    end_value = index_series.iloc[-1]
    return (end_value / start_value - 1) * 100

portfolio_perf_yesterday = calculate_performance(portfolio_index, 1)
portfolio_perf_1y = calculate_performance(portfolio_index, 365)
portfolio_perf_3y = calculate_performance(portfolio_index, 3*365)

portfolio_hedged_perf_yesterday = calculate_performance(portfolio_index_hedged, 1)
portfolio_hedged_perf_1y = calculate_performance(portfolio_index_hedged, 365)
portfolio_hedged_perf_3y = calculate_performance(portfolio_index_hedged, 3*365)

benchmark_perf_yesterday = calculate_performance(bench_index, 1)
benchmark_perf_1y = calculate_performance(bench_index, 365)
benchmark_perf_3y = calculate_performance(bench_index, 3*365)

# =====================
# Affichage des performances
# =====================
st.subheader("📈 Performances")
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("**Portefeuille**")
    st.metric("Perf de la veille", f"{portfolio_perf_yesterday:.2f}%")
    st.metric("Perf sur 1 an", f"{portfolio_perf_1y:.2f}%")
    st.metric("Perf sur 3 ans", f"{portfolio_perf_3y:.2f}%")
with col2:
    st.markdown("**Portefeuille Hedgé USD**")
    st.metric("Perf de la veille", f"{portfolio_hedged_perf_yesterday:.2f}%")
    st.metric("Perf sur 1 an", f"{portfolio_hedged_perf_1y:.2f}%")
    st.metric("Perf sur 3 ans", f"{portfolio_hedged_perf_3y:.2f}%")
with col3:
    st.markdown("**Benchmark**")
    st.metric("Perf de la veille", f"{benchmark_perf_yesterday:.2f}%")
    st.metric("Perf sur 1 an", f"{benchmark_perf_1y:.2f}%")
    st.metric("Perf sur 3 ans", f"{benchmark_perf_3y:.2f}%")

# =====================
# Metrics globales
# =====================
st.subheader("📊 Statistiques globales")
col1, col2, col3 = st.columns(3)
col1.metric("Perf portefeuille (depuis le début)", f"{(portfolio_index.iloc[-1]-1)*100:.2f}%")
col2.metric("Perf portefeuille hedgé (depuis le début)", f"{(portfolio_index_hedged.iloc[-1]-1)*100:.2f}%")
col3.metric("Perf benchmark (depuis le début)", f"{(bench_index.iloc[-1]-1)*100:.2f}%")

st.caption("Mise à jour automatique toutes les heures")
