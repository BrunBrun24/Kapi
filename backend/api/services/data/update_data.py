from collections import defaultdict
import os
import django
import sys

import pandas as pd

from django.contrib.auth import get_user_model

# Chemin vers le dossier racine du projet (là où se trouve manage.py)
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')  # Remplace par le nom de ton projet
django.setup()

from api.models import PortfolioTransaction, PortfolioTicker, PortfolioPerformance, Portfolio, StockPrice
from api.services.modules_copy.portefeuille_bourse import PortefeuilleBourse
from api.services.modules.portfolios.my_portfolio import MyPortfolio, BasePortfolio
from api.services.modules.portfolios.dollar_cost_averaging import DollarCostAveraging


users = [u for u in Portfolio.objects.exclude(name="Trade Republic").values()]
print(users)

tickers_prices = StockPrice.get_open_prices_dataframe_for_all_users()

# for portfolio in users:
#     portefeuille = PortefeuilleBourse(user_id=portfolio["user_id"], portfolio_id=portfolio['id'], tickers_prices=tickers_prices)






def save_performance_tickers(all_performance: dict, performance: pd.DataFrame, portfolio_name: str):
    for key in [
        "tickers_invested_amounts",
        "tickers_twr",
        "tickers_gain",
        "tickers_valuation",
        "tickers_dividends",
        "tickers_pru",
    ]:
        if portfolio_name in all_performance[key]:
            # concaténer les nouvelles données avec l'existant
            all_performance[key][portfolio_name] = pd.concat(
                [all_performance[key][portfolio_name], performance[key]]
            )
        else:
            # première insertion
            all_performance[key][portfolio_name] = performance[key]

def save_performance_benchmarks(all_performance: dict, performance: pd.DataFrame, portfolio_name: str):
    for key in [
        "tickers_invested_amounts",
        "tickers_twr",
        "tickers_gain",
        "tickers_valuation",
        "tickers_dividends",
        "tickers_pru"
    ]:
        if portfolio_name in all_performance[key]:
            # concaténer les nouvelles données avec l'existant
            all_performance[key][portfolio_name] = pd.concat(
                [all_performance[key][portfolio_name], performance[key]]
            )
        else:
            # première insertion
            all_performance[key][portfolio_name] = performance[key]

    for key in {
        "portfolio_twr",
        "portfolio_gain",
        "portfolio_monthly_percentages",
        "portfolio_valuation",
        "portfolio_invested_amounts",
        "portfolio_cash",

        "portfolio_fees",
        "portfolio_cagr",
        "portfolio_dividend_yield",
        "portfolio_dividend_earn"
    }:
        all_performance[key][portfolio_name] = performance[key]


def convert_df_to_json(df: pd.DataFrame):
    """
    Transforme un DataFrame avec index datetime et colonnes de portefeuilles
    en une liste de dictionnaires pour JSONField.

    Exemple de DataFrame en entrée :
                    My Portfolio  Another Portfolio
    2025-06-10        994.033997         875.233444
    2025-06-11        964.138217         885.456789

    Résultat :
    [
        {'date': '2025-06-10', 'My Portfolio': 994.033997, 'Another Portfolio': 875.233444},
        {'date': '2025-06-11', 'My Portfolio': 964.138217, 'Another Portfolio': 885.456789}
    ]
    """
    # S'assurer que l'index est bien en datetime
    if not pd.api.types.is_datetime64_any_dtype(df.index):
        df = df.copy()
        df.index = pd.to_datetime(df.index)

    df.fillna(0, inplace=True)

    formatted_list = []
    for date, row in df.iterrows():
        entry = {'date': date.strftime('%Y-%m-%d')}
        entry.update(row.to_dict())
        formatted_list.append(entry)

    return formatted_list

def convert_data_to_json(data: dict):
    result = []
    for portfolio, df in data.items():
        result.append([portfolio, convert_df_to_json(df)])

    return result

def convert_data_monthly_percentage_to_json(df: pd.DataFrame):
    # ➤ Assure que l'index est en datetime
    if not pd.api.types.is_datetime64_any_dtype(df.index):
        df.index = pd.to_datetime(df.index)

    # Transformation vers dictionnaire structuré
    result = defaultdict(lambda: defaultdict(dict))

    for date, row in df.iterrows():
        year = str(date.year)
        month_abbr = date.strftime("%b")  # "Jan", "Feb", etc.
        for col in df.columns:
            result[col][year][month_abbr] = row[col]

    # ➤ Conversion en dict Python simple (pas defaultdict)
    return {k: dict(v) for k, v in result.items()}

def save_portfolio_performance(user, portfolio, performances: dict):
    User = get_user_model()
    user_instance = User.objects.get(id=user.id)
    portfolio_instance = Portfolio.objects.get(id=portfolio.id)

    PortfolioPerformance.objects.update_or_create(
        user=user_instance,
        portfolio=portfolio_instance,
        defaults={
            "tickers_invested_amounts": convert_data_to_json(performances["tickers_invested_amounts"]),
            "tickers_twr": convert_data_to_json(performances["tickers_twr"]),
            "tickers_gain": convert_data_to_json(performances["tickers_gain"]),
            "tickers_valuation": convert_data_to_json(performances["tickers_valuation"]),
            "tickers_dividends": convert_data_to_json(performances["tickers_dividends"]),
            "tickers_pru": convert_data_to_json(performances["tickers_pru"]),

            "portfolio_twr": convert_df_to_json(performances["portfolio_twr"]),
            "portfolio_gain": convert_df_to_json(performances["portfolio_gain"]),
            "portfolio_monthly_percentages": convert_data_monthly_percentage_to_json(
                performances["portfolio_monthly_percentages"]
            ),
            "portfolio_valuation": convert_df_to_json(performances["portfolio_valuation"]),
            "portfolio_invested_amounts": convert_df_to_json(performances["portfolio_invested_amounts"]),
            "portfolio_cash": convert_df_to_json(performances["portfolio_cash"]),
            "portfolio_fees": convert_df_to_json(performances["portfolio_fees"]),

            "portfolio_cagr": performances["portfolio_cagr"],
            "portfolio_dividend_yield": performances["portfolio_dividend_yield"],
            "portfolio_dividend_earn": performances["portfolio_dividend_earn"],
        }
    )

def save_portfolio_performance_empty(user, portfolio):
    User = get_user_model()
    user_instance = User.objects.get(id=user.id)
    portfolio_instance = Portfolio.objects.get(id=portfolio.id)

    PortfolioPerformance.objects.update_or_create(
        user=user_instance,
        portfolio=portfolio_instance,
        defaults={
            "tickers_invested_amounts": {},
            "tickers_twr": {},
            "tickers_gain": {},
            "tickers_valuation": {},
            "tickers_dividends": {},
            "tickers_pru": {},

            "portfolio_twr": {},
            "portfolio_gain": {},
            "portfolio_monthly_percentages": {},
            "portfolio_valuation": {},
            "portfolio_invested_amounts": {},
            "portfolio_cash": {},
            "portfolio_fees": {},

            "portfolio_cagr": {},
            "portfolio_dividend_yield": {},
            "portfolio_dividend_earn": {},
        }
    )

if __name__ == "__main__":
    # Récupérer les utilisateurs distincts qui ont un portefeuille
    user_ids = Portfolio.objects.values_list("user_id", flat=True).distinct()
    User = get_user_model()

    # On récupère les données boursières de tous les tickers utilisée par les utilisateurs
    tickers = PortfolioTicker.get_all_unique_tickers()
    tickers_open_prices = StockPrice.get_open_prices_dataframe_for_tickers(tickers)

    # On itère par utilisateur
    for user_id in user_ids:
        user = User.objects.get(pk=user_id)
        portfolios = Portfolio.objects.filter(user=user)
        transaction_existe = False

        # On itère par portefeuille de l'utilisateur
        for portfolio in portfolios:
            performances = {
                "tickers_invested_amounts": {},
                "tickers_twr": {},
                "tickers_gain": {},
                "tickers_valuation": {},
                "tickers_dividends": {},
                "tickers_pru": {},

                "portfolio_twr": pd.DataFrame(dtype=float),
                "portfolio_gain": pd.DataFrame(dtype=float),
                "portfolio_monthly_percentages": pd.DataFrame(dtype=float),
                "portfolio_valuation": pd.DataFrame(dtype=float),
                "portfolio_invested_amounts": pd.DataFrame(dtype=float),
                "portfolio_cash": pd.DataFrame(dtype=float),

                "portfolio_fees": pd.DataFrame(dtype=float),
                "portfolio_cagr": {},
                "portfolio_dividend_yield": {},
                "portfolio_dividend_earn": {},
            }

            performances_tickers_eur = {
                "tickers_invested_amounts": {},
                "tickers_twr": {},
                "tickers_gain": {},
                "tickers_valuation": {},
                "tickers_dividends": {},
                "tickers_pru": {},
            }

            # Récupère les tickers par devise
            currencies_tickers = PortfolioTicker.get_user_tickers_by_currency(user_id=user.id, portfolio_id=portfolio.id)

            for currency, tickers in currencies_tickers.items():
                # Récupère les transactions liées au portefeuille d'après sa devise
                transactions = PortfolioTransaction.get_transactions_dataframe(user=user.id, portfolio=portfolio.id, currency=currency)

                # Modifie le dataFrame pour les open price pour ne prendre que les tickers liés aux transactions
                tickers_open_prices_transactions = tickers_open_prices.loc[:, tickers_open_prices.columns.intersection(tickers)]

                # Convertir les données des prix d'ouverture si nécessaire
                tickers_open_prices_transactions = StockPrice.convert_dataframe_to_currency(tickers_open_prices_transactions, currency)

                # Nom du portefeuille de l'utilisateur
                portfolio_name = Portfolio.get_user_portfolio_name(user.id, portfolio.id)

                if not transactions.empty:
                    transaction_empty = True
                    # Récupère les données de performance
                    portefeuille_bourse = MyPortfolio(transactions_df=transactions, tickers_prices=tickers_open_prices_transactions)
                    results = portefeuille_bourse.get_performances()
                    save_performance_tickers(performances, results, portfolio_name)

                    if currency == "EUR":
                        save_performance_tickers(performances_tickers_eur, results, portfolio_name)
                    elif currency == "USD":
                        # Convertir les performances en EUR
                        for key, df in results.items:
                            if key != "tickers_twr":
                                StockPrice.convert_dataframe_to_currency(df, currency)

                        save_performance_tickers(performances_tickers_eur, results, portfolio_name)

            if transaction_empty:
                # Calcule la performance du portefeuille
                start_date, _ = PortfolioTransaction.first_and_last_date(user.id, portfolio.id)
                end_date = pd.to_datetime(tickers_open_prices.index[-1])
                calcul_portfolio = BasePortfolio(start_date=start_date, end_date=end_date)
                portfolio_valuation = performances_tickers_eur["tickers_valuation"][portfolio_name].sum(axis=1)
                portfolio_invested_amounts = performances_tickers_eur["tickers_invested_amounts"][portfolio_name].sum(axis=1)
                transactions_eur = PortfolioTransaction.get_transactions_in_eur(user.id, portfolio.id)
                
                portfolio_realized_gains_losses = calcul_portfolio.compute_plus_value_evolution(transactions_eur, performances_tickers_eur["tickers_invested_amounts"][portfolio_name])["plus_value_cumulative"]
                portfolio_gain = performances_tickers_eur["tickers_gain"][portfolio_name].sum(axis=1) + portfolio_realized_gains_losses
                # L'argent investi correspond à l'argent investi dans les tickers en enlevant les plus et moins values réalisées
                invested_money = (performances_tickers_eur["tickers_invested_amounts"][portfolio_name].sum(axis=1).iloc[-1] - portfolio_realized_gains_losses.iloc[-1])
                portfolio_gain_pct = calcul_portfolio.calculate_portfolio_percentage_change(portfolio_gain, invested_money)

                performances["portfolio_valuation"][portfolio_name] = portfolio_valuation
                performances["portfolio_invested_amounts"][portfolio_name] = portfolio_invested_amounts
                performances["portfolio_gain"][portfolio_name] = portfolio_gain
                performances["portfolio_twr"][portfolio_name] = portfolio_gain_pct
                performances["portfolio_monthly_percentages"][portfolio_name] = calcul_portfolio.calculate_monthly_percentage_change(
                    portfolio_valuation,
                    transactions_eur
                )
                performances["portfolio_dividend_earn"][portfolio_name] = calcul_portfolio.calculate_dividend_earn(transactions_eur)
                performances["portfolio_dividend_yield"][portfolio_name] = calcul_portfolio.calculate_dividend_yield(transactions_eur, portfolio_valuation)
                performances["portfolio_cash"][portfolio_name] = calcul_portfolio.compute_cash_evolution(transactions_eur)["cash_cumulative"]
                performances["portfolio_fees"][portfolio_name] = calcul_portfolio.compute_fees_evolution(transactions_eur)["cumulative_fees"]

                # Comparaison du portefeuille avec les benchmarcks
                portfolios_allocation = [
                    [{'SPY': 100}, 'S&P 500'],
                    [{'NQ=F': 100}, 'Nasdaq 100'],
                    [{'URTH': 100}, 'MSCI WORLD'],
                    [{'^FCHI': 100}, 'CAC 40'],
                ]
                tickers_portfolio_allocation = sorted(set([ticker for portfolio in portfolios_allocation for ticker in portfolio[0].keys()]))
                # Colonnes déjà présentes
                existing_tickers = [t for t in tickers_portfolio_allocation if t in tickers_open_prices.columns]
                # Colonnes manquantes à aller chercher
                missing_tickers = [t for t in tickers_portfolio_allocation if t not in tickers_open_prices.columns]
                # On garde les colonnes existantes
                df_existing = tickers_open_prices[existing_tickers].copy() if existing_tickers else pd.DataFrame()
                # On récupère les colonnes manquantes depuis StockPrice
                df_missing = StockPrice.get_open_prices_dataframe_for_tickers(missing_tickers) if missing_tickers else pd.DataFrame()
                # Fusion (index = dates)
                benchmarks_prices = pd.concat([df_existing, df_missing], axis=1)
                # S'assurer que l'ordre des colonnes correspond à tickers_portfolio_allocation
                benchmarks_prices = benchmarks_prices[tickers_portfolio_allocation]
                # Convertir les données des prix d'ouverture en EUR
                benchmarks_prices = StockPrice.convert_dataframe_to_currency(benchmarks_prices, "EUR")
                money = calcul_portfolio.initial_invested_amount(transactions_eur, performances_tickers_eur["tickers_invested_amounts"][portfolio_name])

                dollar_cost_averaging = DollarCostAveraging(start_date=start_date, end_date=end_date)
                for portfolio_allocation in portfolios_allocation:
                    dollar_cost_averaging.dca(portfolio_allocation, benchmarks_prices, money)
                    benchmarks_performances = dollar_cost_averaging.get_performances()
                    save_performance_benchmarks(performances, benchmarks_performances, portfolio_allocation[-1])

                # Enregistre les perforlances dans la base de donnée
                save_portfolio_performance(user, portfolio, performances)

            else:
                save_portfolio_performance_empty()
