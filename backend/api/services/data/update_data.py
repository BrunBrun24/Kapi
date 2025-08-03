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


name = "trade republic"
name = "all"
users = [u for u in Portfolio.objects.values() if u["name"].lower() == name]
users = [u for u in Portfolio.objects.values() if u["name"].lower() != "name"]
print(users)

for portfolio in users:
    portefeuille = PortefeuilleBourse(user_id=portfolio["user_id"], portfolio_id=portfolio['id'])
