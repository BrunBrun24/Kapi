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
from api.models import Company

def get_sp500_tickers():
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    response = requests.get(url)
    df = pd.read_html(StringIO(response.text), header=0)[0]  # Utiliser StringIO ici
    sp500_tickers = df['Symbol'].tolist()
    sp500_tickers = [ticker.replace('.', '-') for ticker in sp500_tickers]  # Remplacer les points par des tirets pour yfinance
    return sp500_tickers

def get_cac40_tickers():
    url = "https://en.wikipedia.org/wiki/CAC_40"
    response = requests.get(url)
    df = pd.read_html(StringIO(response.text), header=0)[4]  # Utiliser StringIO ici
    cac40_tickers = df['Ticker'].tolist()
    return cac40_tickers

def create_companies(tickers):
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

        # Vérifier si toutes les données sont vides
        if all(value == None for value in [name, isin, sector, country, website, description, founded_date, stock_exchange]):
            print(f"⚠️ Données insuffisantes pour {ticker}, entreprise ignorée.")
            continue  # Ne pas ajouter cette entreprise

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
            # logo=f"logos/{ticker.upper()}.png"
        )
        company.save()
        print(f"✅ {ticker} ajouté avec succès !")

def update_currencies():
    print("🔄 Mise à jour des devises ...")
    for company in Company.objects.all():
        old_currency = company.currency

        if "." in company.ticker:
            company.currency = "EUR"
        else:
            company.currency = "USD"

        if company.currency != old_currency:  # éviter des saves inutiles
            company.save(update_fields=["currency"])
            print(f"✅ {company.ticker} : {old_currency} → {company.currency}")
        else:
            print(f"➡️ {company.ticker} déjà correct ({company.currency})")

    print("Terminé ✅")


# tickers = get_sp500_tickers() + get_cac40_tickers()
# create_companies(tickers)
tickers = ["NVO", "SW.PA", "PLX.PA", "CSSPX.MI", "PHYMF", "EURUSD=X", "SPY", "NQ=F", "URTH", "^FCHI"]
create_companies(tickers)
print("Terminé ✅")


# from stock.models import Company

# # Filtrer l'entreprise avec le ticker "NVO" et supprimer cette ligne
# company_to_delete = Company.objects.filter(ticker="NVO").first()

# if company_to_delete:
#     company_to_delete.delete()
#     print(f"L'entreprise avec le ticker {company_to_delete.ticker} a été supprimée.")
# else:
#     print("Aucune entreprise trouvée avec le ticker 'NVO'.")
