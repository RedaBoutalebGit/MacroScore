import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Trading Fury", page_icon="📊", layout="wide")
st.subheader("Trading Fury MacroScoring")

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
    'EURUSD', 'AUDUSD', 'GBPUSD', 'NZDUSD', 'USDCAD', 'USDCHF', 'USDJPY', 'GBPAUD', 'GBPCAD', 
    'GBPJPY', 'GBPNZD', 'GBPCHF', 'EURAUD', 'EURCAD', 'EURJPY', 'EURNZD', 'EURCHF', 'AUDJPY', 
    'CADJPY', 'NZDJPY', 'CHFJPY', 'AUDCAD', 'AUDNZD', 'AUDCHF', 'NZDCHF', 'NZDCAD', 'EURGBP'
]
paires_details = {pair: [pair[:3], pair[3:]] for pair in paires}

# Indicators
indicators_list = [
    'GDP Growth Rate', "Inflation Rate MoM", "Interest Rate", "Manufacturing PMI",
    "Services PMI", "Retail Sales MoM", "Unemployment Rate"
]
indicators_last_previous = ["GDP Growth Rate", "Interest Rate", "Manufacturing PMI", "Services PMI", "Retail Sales MoM"]
indicators_previous_last = ["Inflation Rate MoM", 'Unemployment Rate']

@st.cache_data(ttl=3600)
def fetch_data(url, headers):
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching data: {e}")
        return None

def get_currency_from_country(country):
    return country_to_currency.get(country.lower(), "Unknown")

def calculate_result(row):
    if row["indicateur"] in indicators_last_previous:
        diff = row["last"] - row["previous"]
    else:
        diff = row["previous"] - row["last"]
    return 1 if diff > 0 else (-1 if diff < 0 else 0)

def color_gradient(val, min_val, max_val):
    normalized = (val - min_val) / (max_val - min_val) if max_val != min_val else 0.5
    r, g = (1 - normalized) * 255, normalized * 255
    return f'background-color: rgb({int(r)}, {int(g)}, 100)'

# Fetching data
data = []
with st.spinner('Loading data...'):
    for country in countries:
        url = f"https://tradingeconomics.com/{country}/indicators"
        html_content = fetch_data(url, headers)
        if html_content:
            soup = BeautifulSoup(html_content, 'lxml')
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

# Display economic data
table_1 = data.set_index(["currency", "indicateur"]).unstack().swaplevel(axis=1).sort_index(axis=1)
st.title("Economic Data 📈")
st.dataframe(table_1, use_container_width=True)

# Display currency scores
data["score"] = data.apply(calculate_result, axis=1)
table_2 = data.pivot(index='currency', columns='indicateur', values='score')
table_2['Total Score'] = table_2.sum(axis=1)
st.title("Currency Scores 💯")
st.dataframe(table_2)

# Calculate pair scores
table_3 = {"Pair": [], "IR Div.": [], "Final Score": []}
for pair, (curr1, curr2) in paires_details.items():
    ir_div = (table_2.loc[curr1, "Interest Rate"] - table_2.loc[curr2, "Interest Rate"]) if "Interest Rate" in table_2 else 0
    score_diff = table_2.loc[curr1, "Total Score"] - table_2.loc[curr2, "Total Score"]
    table_3["Pair"].append(pair)
    table_3["IR Div."].append(ir_div)
    table_3["Final Score"].append(score_diff + ir_div)

table_3 = pd.DataFrame(table_3).set_index("Pair")
min_val, max_val = table_3["Final Score"].min(), table_3["Final Score"].max()
st.title("Final Pair Scores")
st.dataframe(table_3.style.applymap(lambda val: color_gradient(val, min_val, max_val), subset=["Final Score"]))

# Visualization
st.title("Currency Scores Visualization")
fig = px.bar(table_2.reset_index(), x='currency', y='Total Score', color='Total Score', title="Currency Scores")
st.plotly_chart(fig)

# Download data
st.download_button(
    label="Download Final Pair Scores as CSV",
    data=table_3.to_csv().encode('utf-8'),
    file_name='final_pair_scores.csv',
    mime='text/csv',
)
