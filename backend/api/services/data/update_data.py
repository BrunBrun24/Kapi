import os
import django
import sys

from django.contrib.auth import get_user_model

# Chemin vers le dossier racine du projet (là où se trouve manage.py)
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')  # Remplace par le nom de ton projet
django.setup()

from api.models import Portfolio
from api.services.modules.portfolio_performances import PortfolioPerformances
from api.services.modules.compare_transactions_sp500 import ComparePortfolioSP500


users = [u for u in Portfolio.objects.values()]
print(users)


if __name__ == "__main__":
    # Récupérer les utilisateurs distincts qui ont un portefeuille
    user_ids = Portfolio.objects.values_list("user_id", flat=True).distinct()
    User = get_user_model()

    # On itère par utilisateur
    for user_id in user_ids:
        user = User.objects.get(pk=user_id)
        portfolios = Portfolio.objects.filter(user=user)
        
        calcul_portfolio = PortfolioPerformances(user, portfolios)
        # calcul_portfolio = ComparePortfolioSP500(user, portfolios)
