import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# Titre de l'application
st.title("Comparaison d'Allocation vs CAC40")

# Données d'allocation (à adapter selon votre tableau)
allocation_data = {
    "Cash": 5,
    "Actions Europe": 28,  # 5+5+5+4+5+4
    "Actions small & mid": 18,  # 5+4+5+4
    "Actions US": 11,  # 3+2+3+3
    "Fonds alternatif": 16,  # 8+8
    "Fonds Obligataire": 17,  # 9+8
    "Fonds Immobilier": 5,
    "Fonds Actions Pays Emergents": 8,
}

# Fonction pour récupérer les données du CAC40
@st.cache_data
def get_cac40_data():
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    cac40 = yf.Ticker("^FCHI")
    df = cac40.history(start=start_date, end=end_date)
    return df["Close"]

# Récupération des données
cac40_data = get_cac40_data()

# Calcul de la performance de l'allocation (exemple simplifié)
# Ici, on simule une performance linéaire pour l'exemple
allocation_performance = pd.Series(
    data=[sum(allocation_data.values()) * (1 + 0.0005 * i) for i in range(len(cac40_data))],
    index=cac40_data.index
)

# Affichage des données
st.subheader("Allocation actuelle")
st.write(allocation_data)

# Graphique comparatif
fig, ax = plt.subplots()
ax.plot(cac40_data.index, cac40_data, label="CAC40", color="blue")
ax.plot(allocation_performance.index, allocation_performance, label="Mon Allocation", color="red")
ax.set_title("Comparaison de la performance")
ax.set_xlabel("Date")
ax.set_ylabel("Valeur")
ax.legend()
st.pyplot(fig)

# Instructions pour GitHub
st.subheader("Comment héberger sur GitHub ?")
st.write("""
1. Créez un dépôt GitHub.
2. Ajoutez les fichiers `app.py` et `requirements.txt`.
3. Poussez les fichiers sur GitHub.
4. Utilisez un service comme [Streamlit Community Cloud](https://streamlit.io/cloud) pour déployer l'application.
""")
