import json
import os
import sys
import django
import yfinance as yf
import requests
import pandas as pd
from io import StringIO
from concurrent.futures import ThreadPoolExecutor

# Ajouter le chemin au répertoire src pour accéder correctement aux modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

# Définir les paramètres de l'environnement pour Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

# Importer le modèle
from api.models import Company

TICKERS_FILE = "tickers.json"
MISSING_TICKERS_FILE = "missing_tickers.json"

# Charger les tickers à traiter
with open(TICKERS_FILE, "r", encoding="utf-8") as f:
    tickers_data = json.load(f)
tickers_list = [item["ticker"] for item in tickers_data]

# Charger les tickers manquants précédemment
if os.path.exists(MISSING_TICKERS_FILE) and os.path.getsize(MISSING_TICKERS_FILE) > 0:
    with open(MISSING_TICKERS_FILE, "r", encoding="utf-8") as f:
        missing_tickers = set(json.load(f))
else:
    missing_tickers = set()


# Filtrer les tickers déjà marqués comme manquants
tickers_list = [t for t in tickers_list if t not in missing_tickers]

def create_companies(tickers):
    global missing_tickers
    print("En cours ...")
    for ticker in tickers:
        if Company.objects.filter(ticker=ticker).exists():
            continue

        stock = yf.Ticker(ticker)
        info = stock.info

        name = info.get('shortName')
        isin = info.get('isin')
        sector = info.get('sector')
        country = info.get('country')
        website = info.get('website')
        description = info.get('longBusinessSummary')
        founded_date = info.get('yearBorn')
        stock_exchange = info.get('exchange')

        # Vérifier si le nom est présent
        if not name:
            print(f"⚠️ Nom manquant pour {ticker}, entreprise ignorée.")
            missing_tickers.add(ticker)
            with open(MISSING_TICKERS_FILE, "w", encoding="utf-8") as f:
                json.dump(list(missing_tickers), f, indent=2)

            continue

        # Vérifier si toutes les données sont vides
        if all(value is None for value in [name, isin, sector, country, website, description, founded_date, stock_exchange]):
            print(f"⚠️ Données insuffisantes pour {ticker}, entreprise ignorée.")
            missing_tickers.add(ticker)
            with open(MISSING_TICKERS_FILE, "w", encoding="utf-8") as f:
                json.dump(list(missing_tickers), f, indent=2)

            continue

        # Création et sauvegarde de l'entreprise
        company = Company(
            name=name,
            ticker=ticker,
            isin=isin,
            sector=sector,
            country=country,
            website=website,
            description=description,
            founded_date=founded_date,
            stock_exchange=stock_exchange,
        )
        company.save()
        print(f"✅ {ticker} ajouté avec succès !")

create_companies(tickers_list)
print("Terminé ✅")