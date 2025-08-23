from datetime import datetime
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
from api.models import Company, Dividend, StockPrice, StockSplit  # adapte le chemin si nécessaire
from django.db import IntegrityError, transaction
from django.utils.dateparse import parse_date

def fetch_and_store_all_dividends():
    tickers = list(Company.objects.values_list("ticker", flat=True))

    if not tickers:
        print("Aucun ticker trouvé dans la base de données.")
        return

    for ticker_str in tickers:
        try:
            company = Company.objects.get(ticker=ticker_str)
            stock = yf.Ticker(ticker_str)
            dividends = stock.dividends  # pandas Series (index = date, value = amount)

            if dividends.empty:
                continue

            for date, amount in dividends.items():
                try:
                    Dividend.objects.update_or_create(
                        ticker=company,
                        date=date,
                        defaults={
                            "amount": round(float(amount), 2)
                        }
                    )
                except IntegrityError:
                    print(f"Conflit pour {ticker_str} à la date {date}")
                    continue

            print(f"Dividendes importés pour {ticker_str}")

        except Exception as e:
            print(f"Erreur pour {ticker_str} : {e}")


fetch_and_store_all_dividends()