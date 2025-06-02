import os
import django
import sys


# Chemin vers le dossier racine du projet (là où se trouve manage.py)
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')  # Remplace par le nom de ton projet
django.setup()

from api.models import PortfolioTransaction, PortfolioTicker, PortfolioPerformance, Portfolio
from api.services.modules.portefeuille_bourse import PortefeuilleBourse


users = list(Portfolio.objects.filter().values())
print(users)

# for portfolio in users:
#     portefeuille = PortefeuilleBourse(user_id=portfolio["user_id"], portfolio_id=portfolio['id'])


import pandas as pd
from typing import Any


@staticmethod
def _deserialize_value(value: Any) -> Any:
    # Remettre les types utiles si besoin (ex : float/int ou datetime)
    if isinstance(value, str):
        try:
            return pd.to_datetime(value)
        except ValueError:
            return value
    return value

def deserialize_simple_dataframe(serialized_df: dict[str, dict[str, Any]]) -> pd.DataFrame:
    data = {
        idx: {
            col: _deserialize_value(val)
            for col, val in row.items()
        }
        for idx, row in serialized_df.items()
    }
    df = pd.DataFrame.from_dict(data, orient="index")
    df.index.name = None
    return df


def json_dict_to_dataframe_dict(json_data):
    result = {}
    for key, data in json_data.items():
        df = pd.DataFrame.from_dict(data, orient="index")

        # Tenter de parser l’index en datetime si possible
        try:
            df.index = pd.to_datetime(df.index)
        except Exception:
            pass

        result[key] = df
    return result

def json_to_dataframe(data: dict) -> pd.DataFrame:
    """
    Convertit un dict JSON-compatible (issu de la DB) en DataFrame.
    L'index est reconverti en datetime.
    """
    df = pd.DataFrame.from_dict(data, orient="index")
    df.index = pd.to_datetime(df.index)
    return df


# Récupération de la performance d’un utilisateur
performance = PortfolioPerformance.objects.filter(user=1).first()

if performance:
    portfolio_twr = json_to_dataframe(performance.portfolio_twr)
    print(portfolio_twr)

    ticker_twr = json_dict_to_dataframe_dict(performance.twr_by_ticker)
    print(ticker_twr)
else:
    print("Aucune performance trouvée pour l'utilisateur.")



