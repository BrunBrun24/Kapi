from datetime import datetime
import os
import django
import sys

import pandas as pd


# Chemin vers le dossier racine du projet (là où se trouve manage.py)
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')  # Remplace par le nom de ton projet
django.setup()

from api.models import PortfolioTransaction, PortfolioTicker, PortfolioPerformance, Portfolio
from api.services.modules.portefeuille_bourse import PortefeuilleBourse


users = list(Portfolio.objects.values())
print(users)

for portfolio in users:
    portefeuille = PortefeuilleBourse(user_id=portfolio["user_id"], portfolio_id=portfolio['id'])

# user_portfolios = list(
#     Portfolio.objects
#     .filter(user=1)
#     .exclude(name="My Portfolio")
#     .values()
# )
# print(user_portfolios)

# all_transactions = pd.DataFrame()

# for portfolio in user_portfolios:
#     transactions = pd.DataFrame(PortfolioTransaction.objects.filter(
#         user_id=portfolio["user_id"],
#         portfolio_id=portfolio["id"]
#     ).order_by("date").values())
    
#     all_transactions = pd.concat([all_transactions, transactions], ignore_index=True)
#     print(transactions)
#     print()

# all_transactions['date'] = pd.to_datetime(all_transactions['date'])
# all_transactions = all_transactions.sort_values(by='date')
# print(all_transactions)
