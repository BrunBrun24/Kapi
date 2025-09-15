import os
import django
import sys

from django.contrib.auth import get_user_model

# Chemin vers le dossier racine du projet (là où se trouve manage.py)
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')  # Remplace par le nom de ton projet
django.setup()

from api.models import Portfolio, PortfolioTicker, TickerPerformanceCompareSP500

p = Portfolio.objects.get(id=1)
pt = PortfolioTicker.objects.get(portfolio=p, ticker__ticker="AAPL")
TickerPerformanceCompareSP500.objects.filter(portfolio=p, ticker=pt).values()
