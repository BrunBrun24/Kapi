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
from api.models import Company, StockPrice, StockSplit  # adapte le chemin si nécessaire
from django.db import transaction
from django.utils.dateparse import parse_date


def import_stock_prices(start_date="1800-01-01", end_date=None):
    if end_date is None:
        end_date = datetime.today().strftime("%Y-%m-%d")

    tickers = list(Company.objects.values_list("ticker", flat=True))
    if not tickers:
        print("Aucun ticker trouvé dans la base de données.")
        return

    print(f"Téléchargement des données pour {len(tickers)} tickers...")

    # Téléchargement groupé via yfinance
    data = yf.download(
        tickers=tickers,
        start=start_date,
        end=end_date,
        group_by='ticker',
        auto_adjust=False,
        threads=True,
        progress=True,
    )

    with transaction.atomic():
        for ticker in tickers:
            try:
                ticker_data = data[ticker]
            except KeyError:
                print(f"❌ Données manquantes pour {ticker}")
                continue

            # Récupérer toutes les dates déjà présentes pour ce ticker
            existing_dates = set(
                StockPrice.objects.filter(ticker_id=ticker)
                .values_list("date", flat=True)
            )

            new_rows = 0
            for date, row in ticker_data.iterrows():
                current_date = date.date()
                if current_date in existing_dates:
                    continue  # Ne pas modifier les lignes existantes

                if pd.isnull(row["Close"]):
                    continue  # Skip les lignes sans prix

                StockPrice.objects.create(
                    ticker_id=ticker,
                    date=current_date,
                    open_price=row["Open"],
                    high_price=row["High"],
                    low_price=row["Low"],
                    close_price=row["Close"],
                    volume=int(row["Volume"]) if not pd.isnull(row["Volume"]) else 0,
                )
                new_rows += 1

            print(f"✅ {ticker} : {new_rows} nouvelles lignes ajoutées")

    print("✅ Import terminé.")

def update_splits_for_all_companies():
    companies = Company.objects.all()

    for company in companies:
        ticker_str = company.ticker
        print(f"📥 Téléchargement des splits pour {ticker_str}")

        try:
            splits = yf.Ticker(ticker_str).splits  # Series: index=date, values=ratio

            if splits.empty:
                print(f"❌ Aucun split trouvé pour {ticker_str}")
                continue

            # Récupérer les dates de split déjà présentes pour éviter les doublons
            existing_dates = set(
                StockSplit.objects.filter(ticker=company)
                .values_list("date", flat=True)
            )

            new_splits = 0
            for date, ratio in splits.items():
                split_date = parse_date(str(date.date()))
                if split_date in existing_dates:
                    continue  # Split déjà existant, on ignore

                StockSplit.objects.create(
                    ticker=company,
                    date=split_date,
                    ratio=float(ratio)
                )
                new_splits += 1

            print(f"✅ {ticker_str} : {new_splits} nouveaux splits ajoutés")

        except Exception as e:
            print(f"⚠️ Erreur pour {ticker_str} : {e}")


# import_stock_prices()
update_splits_for_all_companies()