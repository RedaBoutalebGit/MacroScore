import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np


st.set_page_config(page_title="Trading Fury",page_icon="📊",layout="wide",)
st.subheader("Trading Fury MacroScoring")

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36','Accept-Language': 'en-US,en;q=0.9','Accept-Encoding': 'gzip, deflate, br'}

# Data about countries and currencies
countries = ["australia","canada","euro-area", "united-kingdom", "japan", "new-zealand","united-states", "switzerland"]
currencies = ["AUD", "CAD", "EUR", "GBP", "JPY", "NZD", "USD", "CHF"]
country_to_currency = dict(zip(countries, currencies))
currency_to_country = dict(zip(currencies, countries))
# Pairs
paires = ['EURUSD', 'AUDUSD', 'GBPUSD', 'NZDUSD', 'USDCAD', 'USDCHF', 'USDJPY', 'GBPAUD', 'GBPCAD', 'GBPJPY', 'GBPNZD', 'GBPCHF', 'EURAUD', 'EURCAD', 'EURJPY', 'EURNZD', 'EURCHF', 'AUDJPY', 'CADJPY', 'NZDJPY', 'CHFJPY', 'AUDCAD', 'AUDNZD', 'AUDCHF', 'NZDCHF', 'NZDCAD', 'EURGBP', ]
paires_details = {}
for pair in paires:
    part1 = pair[:3]
    part2 = pair[3:]
    paires_details[pair] = [part1, part2]
# Indicators
indicators_list = ['GDP Growth Rate', "Inflation Rate MoM", "Interest Rate", "Manufacturing PMI","Services PMI","Retail Sales MoM", "Unemployment Rate"]
indicators_last_previous = ["GDP Growth Rate", "Interest Rate", "Manufacturing PMI", "Services PMI", "Retail Sales MoM"]
indicators_previous_last = ["Inflation Rate MoM",'Unemployment Rate']
# Functions
def get_currency_from_country(country):
    return country_to_currency.get(country.lower(), "Pays inconnu")
def get_country_from_currency(currency):
    return currency_to_country.get(currency.upper(), "Devise inconnue")
def calculate_result(row):
    if row["indicateur"] in indicators_last_previous:
        diff = row["last"] - row["previous"]
        if diff == 0:
            return 0
        elif diff > 0:
            return 1
        else:
            return -1
    elif row["indicateur"] in indicators_previous_last:
        diff = row["previous"] - row["last"]
        if diff == 0:
            return 0
        elif diff > 0:
            return 1
        else:
            return -1
def color_gradient(val, min_val, max_val):
    # Plages définies
    red_min, red_max = min_val, 0   # Plage rouge : entre -10 et 0
    green_min, green_max = 0, max_val  # Plage verte : entre 0 et 10

    # Définir les couleurs pour les extrêmes
    color_red_min = np.array([243, 35, 35])  # #EE1616
    color_red_max = np.array([233, 172, 172])   # Rouge foncé
    color_green_min = np.array([193, 238, 191])  # Blanc pour 0
    color_green_max = np.array([64, 176, 61])  # #0E6B24

    # Si la valeur est exactement 0, on retourne le blanc
    if val == 0:
        return 'background-color: white'
    
    # Interpolation pour les valeurs négatives (Rouge)
    if val < 0:
        norm_val_red = (val - red_min) / (red_max - red_min)
        interpolated_color_red = (1 - norm_val_red) * color_red_min + norm_val_red * color_red_max
        interpolated_color_red = interpolated_color_red.astype(int)
        color_hex = f'rgb({interpolated_color_red[0]}, {interpolated_color_red[1]}, {interpolated_color_red[2]})'
    
    # Interpolation pour les valeurs positives (Vert)
    elif val > 0:
        norm_val_green = (val - green_min) / (green_max - green_min)
        interpolated_color_green = (1 - norm_val_green) * color_green_min + norm_val_green * color_green_max
        interpolated_color_green = interpolated_color_green.astype(int)
        color_hex = f'rgb({interpolated_color_green[0]}, {interpolated_color_green[1]}, {interpolated_color_green[2]})'
    
    return f'background-color: {color_hex}'

#col1, col2, col3 = st.columns(3)
#with col1:
 #   st.write("List of currencies:")
  #  st.dataframe(pd.DataFrame({"Country": countries, "Currencies": currencies}).set_index("Country"))
#with col2:
 #   st.write("List of pairs:")
  #  colA, colB = st.columns(2)
   # mid_index = len(paires) // 2
    #with colA:
     #   st.write(paires[:mid_index])
    #with colB:
     #   st.write(paires[mid_index:])
#with col3:
 #   st.write("List of indicators:", indicators_list)
#
# Scrap
data = []
with st.spinner('Chargement des données...'):
    for i,country in enumerate(countries):
        url = f"https://tradingeconomics.com/{country}/indicators" 
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            html_content = response.text
            soup = BeautifulSoup(html_content, 'lxml')
            rows = soup.select('tbody > tr')
            for row in rows:
                cols = row.find_all('td')
                if cols[0].get_text(strip=True) in indicators_list:
                    row_data = {
                        'indicateur': cols[0].get_text(strip=True),
                        'last': float(cols[1].get_text(strip=True)),
                        'previous': float(cols[2].get_text(strip=True)),
                        # 'le_plus_élevé': cols[3].get_text(strip=True),
                        # 'le_plus_bas': cols[4].get_text(strip=True),
                        # 'unité': cols[5].get_text(strip=True),
                        # 'date': cols[6].get_text(strip=True),
                        'currency': get_currency_from_country(country)
                    }
                    data.append(row_data)
        else:
            print(f"Erreur lors de la récupération de la page. Code HTTP : {response.status_code}")
data = pd.DataFrame(data).drop_duplicates()
table_1 = (data.set_index(["currency", "indicateur"]).stack().unstack(level=[1, 2]))
table_1.columns = pd.MultiIndex.from_tuples([(indicateur, stat) for indicateur, stat in table_1.columns],names=["indicateur", ""])
sort_list = []
for indic in indicators_list:
    sort_list.append((indic, 'last'))
    sort_list.append((indic, 'previous'))
table_1 = table_1[sort_list]
table_1 = table_1.reindex([get_currency_from_country(count) for count in countries])
st.title("Economic Data 📈")
st.dataframe(table_1,use_container_width =True)


table_2 = data.copy()
table_2["score"] = table_2.apply(calculate_result, axis=1)
table_2 = table_2[["indicateur", "currency", "score"]]
table_2 = table_2.pivot(index='currency', columns='indicateur', values='score')
table_2['score'] = table_2.sum(axis=1)
columns_table_2 = indicators_list.copy()
columns_table_2.insert(0, "score")
table_2 = table_2[columns_table_2]
table_2 = table_2.reindex([get_currency_from_country(count) for count in countries])
st.title("Currencies score💯")
st.dataframe(table_2)


table_3 = {"Paire": [],"IR Div.": [], "Score Final": []}
for pair in paires:
    previous_value_pair1 = data[(data["indicateur"]=="Interest Rate")&(data["currency"]==paires_details[pair][0])]["last"].values[0]
    previous_value_pair2 = data[(data["indicateur"]=="Interest Rate")&(data["currency"]==paires_details[pair][1])]["last"].values[0]
    table_3['Paire'].append(pair)
    if previous_value_pair1>previous_value_pair2:
        ir_div = 1
    elif previous_value_pair1<previous_value_pair2:
        ir_div = -1
    else:
        ir_div = 0
    score_final = table_2[table_2.index==paires_details[pair][0]]["score"].values[0] - table_2[table_2.index==paires_details[pair][1]]["score"].values[0] + ir_div
    table_3['IR Div.'].append(ir_div)
    table_3['Score Final'].append(score_final)
table_3 = pd.DataFrame(table_3).set_index("Paire")
st.title("Final scoring:")
st.dataframe(table_3.style.applymap(lambda val: color_gradient(val, table_3["Score Final"].min(), table_3["Score Final"].max()), subset=['Score Final']))
