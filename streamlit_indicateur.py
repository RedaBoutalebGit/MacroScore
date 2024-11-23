import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np

st.set_page_config(page_title="Indicateur Trading", page_icon="📊", layout="wide")

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br'
}

# Data about countries and currencies
countries = ["australia", "canada", "euro-area", "united-kingdom", "japan", "new-zealand", "united-states", "switzerland"]
currencies = ["AUD", "CAD", "EUR", "GBP", "JPY", "NZD", "USD", "CHF"]
country_to_currency = dict(zip(countries, currencies))
currency_to_country = dict(zip(currencies, countries))

# Pairs
paires = [
    'EURUSD', 'AUDUSD', 'GBPUSD', 'NZDUSD', 'USDCAD', 'USDCHF', 'USDJPY',
    'GBPAUD', 'GBPCAD', 'GBPJPY', 'GBPNZD', 'GBPCHF', 'EURAUD', 'EURCAD',
    'EURJPY', 'EURNZD', 'EURCHF', 'AUDJPY', 'CADJPY', 'NZDJPY', 'CHFJPY',
    'AUDCAD', 'AUDNZD', 'AUDCHF', 'NZDCHF', 'NZDCAD', 'EURGBP'
]
paires_details = {pair: [pair[:3], pair[3:]] for pair in paires}

# Indicators
indicators_list = ['GDP Growth Rate', "Inflation Rate MoM", "Interest Rate", "Manufacturing PMI", "Services PMI", "Retail Sales MoM", "Unemployment Rate"]
indicators_last_previous = ["GDP Growth Rate", "Interest Rate", "Manufacturing PMI", "Services PMI", "Retail Sales MoM"]
indicators_previous_last = ["Inflation Rate MoM", 'Unemployment Rate']

# Utility functions
def get_currency_from_country(country):
    return country_to_currency.get(country.lower(), "Unknown")

def calculate_result(row):
    if row["indicateur"] in indicators_last_previous:
        return 1 if row["last"] > row["previous"] else -1 if row["last"] < row["previous"] else 0
    elif row["indicateur"] in indicators_previous_last:
        return 1 if row["previous"] > row["last"] else -1 if row["previous"] < row["last"] else 0

# Scrap data
data = []
with st.spinner('Fetching data...'):
    for country in countries:
        url = f"https://tradingeconomics.com/{country}/indicators"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'lxml')
            rows = soup.select('tbody > tr')
            for row in rows:
                cols = row.find_all('td')
                if cols[0].get_text(strip=True) in indicators_list:
                    data.append({
                        'indicateur': cols[0].get_text(strip=True),
                        'last': float(cols[1].get_text(strip=True)),
                        'previous': float(cols[2].get_text(strip=True)),
                        'currency': get_currency_from_country(country)
                    })

data = pd.DataFrame(data).drop_duplicates()

# Calculate scores for each currency
data["score"] = data.apply(calculate_result, axis=1)
currency_scores = data.groupby("currency")["score"].sum().to_dict()

# Navigation between pages
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Search Forex Pair", "Scores Table"])

if page == "Search Forex Pair":
    st.subheader("Search Forex Pair")
    pair_input = st.text_input("Enter Forex Pair (e.g., EURUSD):").upper()
    if pair_input in paires:
        currency1 = paires_details[pair_input][0]
        currency2 = paires_details[pair_input][1]
        
        # Fetch scores and Interest Rate difference
        score1 = currency_scores.get(currency1, 0)
        score2 = currency_scores.get(currency2, 0)
        ir1 = data[(data["indicateur"] == "Interest Rate") & (data["currency"] == currency1)]["last"].values[0]
        ir2 = data[(data["indicateur"] == "Interest Rate") & (data["currency"] == currency2)]["last"].values[0]
        ir_diff = 1 if ir1 > ir2 else -1 if ir1 < ir2 else 0
        
        # Calculate Final Score
        final_score = score1 - score2 + ir_diff

        # Display results
        st.write(f"### Data for Pair: {pair_input}")
        st.write(f"**Currency 1 ({currency1})**")
        st.dataframe(data[data["currency"] == currency1])
        st.write(f"**Currency 2 ({currency2})**")
        st.dataframe(data[data["currency"] == currency2])
        st.write(f"**Final Score**: {final_score}")
    else:
        st.write("Enter a valid Forex Pair to display its data.")

elif page == "Scores Table":
    st.subheader("Scores Table for All Currencies")
    # Create a table summarizing all scores
    score_table = pd.DataFrame(currency_scores.items(), columns=["Currency", "Score"])
    st.dataframe(score_table)
