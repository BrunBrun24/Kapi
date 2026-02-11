from datetime import datetime
import json
import os
import sys
import django
import yfinance as yf
import requests
import pandas as pd
from io import StringIO

# Ajouter le chemin au répertoire src pour accéder correctement aux modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

# Définir les paramètres de l'environnement pour Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

# Importer le modèle
from api.models import Company, Dividend, StockPrice, StockSplit



AV_API_KEY = '782N07W5SK5A1EG0'

def company_overview(symbol, api_key):
    """
    Get company overview data from Alpha Vantage
    Inputs:
    symbol (str) = stock symbol
    api_key (str) = Alpha Vantage API key
    Return dict
    All dict values are strings (even numeric fields)
    """
    url = "https://www.alphavantage.co/query?function=OVERVIEW&symbol={}&apikey={}"
    r = requests.get(url.format(symbol, api_key))
    data = r.json()
    return data

def company_earning(symbol, api_key):
    """
    Récupère les données d'earnings d'une société via l'API Alpha Vantage.
    """
    url = f"https://www.alphavantage.co/query?function=EARNINGS&symbol={symbol}&apikey={api_key}"
    r = requests.get(url)
    data = r.json()
    return data


def save_earnings_to_json(symbols, api_key, output_file):
    """
    Récupère les earnings pour plusieurs tickers et les enregistre dans un fichier JSON.
    
    :param symbols: liste de tickers (ex: ['AAPL', 'MSFT', 'BKNG'])
    :param api_key: clé API Alpha Vantage
    :param output_file: chemin du fichier de sortie JSON
    """
    all_data = {}

    for symbol in symbols:
        print(f"⏳ Téléchargement des earnings pour {symbol}...")
        data = company_earning(symbol, api_key)
        all_data[symbol] = data
        # time.sleep(12)  # ⏱️ AlphaVantage limite à 5 requêtes/minute (gratuit)

    # Enregistrement dans un fichier JSON
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=4)

    print(f"✅ Données enregistrées dans {output_file}")




AV_API_KEY = "TA_CLE_API_ICI"
SYMBOLS = ["AAPL", "MSFT", "BKNG", "GOOGL"]
OUTPUT_FILE = "earnings_data.json"

save_earnings_to_json(SYMBOLS, AV_API_KEY, OUTPUT_FILE)