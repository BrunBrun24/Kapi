from collections import defaultdict
import pandas as pd
from datetime import datetime
from api.models import PortfolioTransaction, PortfolioTicker, PortfolioPerformance, Portfolio, StockPrice
from api.services.modules.portfolios.my_portfolio import MyPortfolio
from django.contrib.auth import get_user_model

from api.services.modules.portfolios.dollar_cost_averaging import DollarCostAveraging
from api.services.modules.portfolios.replication import Replication

class PortefeuilleBourse(MyPortfolio, DollarCostAveraging, Replication):
    def __init__(self, user, portfolios, start_date: datetime = None, tickers_valuations: dict = {}):
        if isinstance(portfolios, int):
            portfolios = Portfolio.objects.filter(pk=portfolios, user=user)
        elif isinstance(portfolios, Portfolio):
            portfolios = [portfolios]

        # On récupère les données boursières de tous les tickers utilisée par les utilisateurs
        tickers = PortfolioTicker.get_all_unique_tickers()
        tickers_open_prices = StockPrice.get_open_prices_dataframe_for_tickers(tickers)

        # On itère par portefeuille de l'utilisateur
        for portfolio in portfolios:
            self.performances = {
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
            transactions_not_empty = False

            for currency, tickers in currencies_tickers.items():
                # Récupère les transactions liées au portefeuille d'après sa devise
                transactions = PortfolioTransaction.get_transactions_dataframe(user=user.id, portfolio=portfolio.id, currency=currency)
                if start_date is not None:
                    transactions = self.set_transaction_with_date(transactions, start_date, tickers_valuations, StockPrice.convert_dataframe_to_currency(tickers_open_prices, currency))

                if not transactions.empty:
                    transactions_not_empty = True
                    if start_date is None:
                        self.start_date = pd.to_datetime(transactions.index[0]).normalize()
                    self.end_date = pd.to_datetime(tickers_open_prices.index[-1]).normalize()

                    # Nom du portefeuille de l'utilisateur
                    portfolio_name = Portfolio.get_user_portfolio_name(user.id, portfolio.id)

                    # Modifie le dataFrame pour les open price pour ne prendre que les tickers liés aux transactions
                    tickers_open_prices_currency = tickers_open_prices.loc[:, tickers_open_prices.columns.intersection(tickers)]
                    # Convertir les données des prix d'ouverture si nécessaire
                    tickers_open_prices_currency = StockPrice.convert_dataframe_to_currency(tickers_open_prices_currency, currency)
                    # Ne prendre que les dates concernées par les transactions
                    tickers_open_prices_currency = tickers_open_prices_currency.loc[self.start_date:]
                    all_dates = pd.date_range(start=self.start_date, end=self.end_date, freq='D')
                    tickers_open_prices_currency = tickers_open_prices_currency.reindex(all_dates).ffill().bfill()

                    # Récupère les données de performance
                    results = self.my_portfolio(transactions_df=transactions, tickers_prices=tickers_open_prices_currency)
                    self.save_performance_tickers(self.performances, results, portfolio_name)

                    if currency == "EUR":
                        self.save_performance_tickers(performances_tickers_eur, results, portfolio_name)
                    elif currency == "USD":
                        # Convertir les performances en EUR
                        for key, df in results.items():
                            if key != "tickers_twr":
                                StockPrice.convert_dataframe_to_currency(df, "EUR")
                        self.save_performance_tickers(performances_tickers_eur, results, portfolio_name)

            if transactions_not_empty:
                # Calcule la performance du portefeuille
                if start_date is None:
                    self.start_date, _ = PortfolioTransaction.first_and_last_date(user.id, portfolio.id)
                self.end_date = pd.to_datetime(tickers_open_prices.index[-1])

                portfolio_valuation = performances_tickers_eur["tickers_valuation"][portfolio_name].sum(axis=1)
                portfolio_invested_amounts = performances_tickers_eur["tickers_invested_amounts"][portfolio_name].sum(axis=1)
                transactions_eur = PortfolioTransaction.get_transactions_in_eur(user.id, portfolio.id)

                if start_date is not None:
                    transactions_eur = self.set_transaction_with_date(transactions_eur, start_date, tickers_valuations, StockPrice.convert_dataframe_to_currency(tickers_open_prices, "EUR"))

                portfolio_realized_gains_losses = self.compute_plus_value_evolution(transactions_eur, performances_tickers_eur["tickers_invested_amounts"][portfolio_name])["plus_value_cumulative"]
                portfolio_gain = performances_tickers_eur["tickers_gain"][portfolio_name].sum(axis=1) + portfolio_realized_gains_losses

                # L'argent investi correspond à l'argent investi dans les tickers en enlevant les plus et moins values réalisées
                invested_money = (performances_tickers_eur["tickers_invested_amounts"][portfolio_name].sum(axis=1).iloc[-1] - portfolio_realized_gains_losses.iloc[-1])
                portfolio_gain_pct = self.calculate_portfolio_percentage_change(portfolio_gain, invested_money)

                self.performances["portfolio_valuation"][portfolio_name] = portfolio_valuation
                self.performances["portfolio_invested_amounts"][portfolio_name] = portfolio_invested_amounts
                self.performances["portfolio_gain"][portfolio_name] = portfolio_gain
                self.performances["portfolio_twr"][portfolio_name] = portfolio_gain_pct
                self.performances["portfolio_monthly_percentages"][portfolio_name] = self.calculate_monthly_percentage_change(portfolio_valuation, transactions_eur)
                self.performances["portfolio_dividend_earn"][portfolio_name] = self.calculate_dividend_earn(transactions_eur)
                self.performances["portfolio_dividend_yield"][portfolio_name] = self.calculate_dividend_yield(transactions_eur, portfolio_valuation)
                self.performances["portfolio_cash"][portfolio_name] = self.compute_cash_evolution(transactions_eur)["cash_cumulative"]
                self.performances["portfolio_fees"][portfolio_name] = self.compute_fees_evolution(transactions_eur)["cumulative_fees"]

                # Comparaison du portefeuille avec les benchmarks
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

                money = self.initial_invested_amount(transactions_eur, performances_tickers_eur["tickers_invested_amounts"][portfolio_name])

                for portfolio_allocation in portfolios_allocation:
                    benchmarks_performances = self.dca(portfolio_allocation, benchmarks_prices, money)
                    self.save_performance_benchmarks(self.performances, benchmarks_performances, portfolio_allocation[-1])

                if start_date is None:
                    # Enregistre les performances dans la base de donnée
                    self.save_portfolio_performance(user, portfolio, self.performances)
            else:
                if start_date is None:
                    self.save_portfolio_performance_empty()



    def set_transaction_with_date(self, transactions_all: pd.DataFrame, start_date: datetime, tickers_valuations: dict, tickers_prices: pd.DataFrame) -> pd.DataFrame:
        start_date = pd.to_datetime(start_date).normalize()
        tickers_prices.index = pd.to_datetime(tickers_prices.index).normalize()
        tickers_prices = tickers_prices.ffill().bfill()

        # Prendre la date la plus proche disponible
        start_date = tickers_prices.index[
            tickers_prices.index.get_indexer([start_date], method='nearest')[0]
        ]
        self.start_date = start_date

        # S'assurer que l'index est bien datetime
        if not isinstance(transactions_all.index, pd.DatetimeIndex):
            transactions_all.index = pd.to_datetime(transactions_all.index)

        # Filtrer transactions
        transactions_after = transactions_all[transactions_all.index >= start_date]

        new_rows = []

        # Création des lignes "buy"
        for ticker, valuation in tickers_valuations.items():
            if float(valuation) != 0:
                stock_price = tickers_prices.loc[start_date, ticker]
                previous_quantity = float(valuation) / stock_price

                new_row = {
                    'id': None,
                    'portfolio_ticker_id': None,
                    'operation': 'buy',
                    'amount': float(valuation),
                    'fees': 0.0,
                    'stock_price': stock_price,
                    'quantity': previous_quantity,
                    'currency': "EUR",
                    'ticker': ticker
                }
                new_rows.append((start_date, new_row))

        # Création DataFrame et fusion
        if new_rows:
            new_df = pd.DataFrame(
                [row for _, row in new_rows],
                index=[date for date, _ in new_rows],
                columns=transactions_after.columns
            )
            new_df.index.name = 'date'
            new_df = new_df.dropna(axis=1, how='all')
            transactions_after = pd.concat([new_df, transactions_after]).sort_index()

        return transactions_after.sort_index()

    def get_performances(self) -> dict:
        return {
            "tickers_invested_amounts": self.tickers_invested_amounts,
            "tickers_sold_amounts": self.tickers_sold_amounts,
            "tickers_twr": self.tickers_twr,
            "tickers_gain": self.tickers_gain,
            "tickers_valuation": self.tickers_valuation,
            "tickers_dividends": self.tickers_dividends,
            "tickers_pru": self.tickers_pru,
            "portfolio_twr": self.portfolio_twr,
            "portfolio_gain": self.portfolio_gain,
            "portfolio_monthly_percentages": self.portfolio_monthly_percentages,
            "portfolio_valuation": self.portfolio_valuation,
            "portfolio_invested_amounts": self.portfolio_invested_amounts,
            "portfolio_cash": self.portfolio_cash,
            "portfolio_fees": self.portfolio_fees,
            "portfolio_cagr": self.portfolio_cagr,
            "portfolio_dividend_yield": self.portfolio_dividend_yield,
            "portfolio_dividend_earn": self.portfolio_dividend_earn,
        }

    @staticmethod
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

    @staticmethod
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

    @staticmethod
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

    def convert_data_to_json(self, data: dict):
        result = []
        for portfolio, df in data.items():
            result.append([portfolio, self.convert_df_to_json(df)])
        return result

    @staticmethod
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

    def save_portfolio_performance(self, user, portfolio, performances: dict):
        User = get_user_model()
        user_instance = User.objects.get(id=user.id)
        portfolio_instance = Portfolio.objects.get(id=portfolio.id)

        PortfolioPerformance.objects.update_or_create(
            user=user_instance,
            portfolio=portfolio_instance,
            defaults={
                "tickers_invested_amounts": self.convert_data_to_json(performances["tickers_invested_amounts"]),
                "tickers_twr": self.convert_data_to_json(performances["tickers_twr"]),
                "tickers_gain": self.convert_data_to_json(performances["tickers_gain"]),
                "tickers_valuation": self.convert_data_to_json(performances["tickers_valuation"]),
                "tickers_dividends": self.convert_data_to_json(performances["tickers_dividends"]),
                "tickers_pru": self.convert_data_to_json(performances["tickers_pru"]),
                "portfolio_twr": self.convert_df_to_json(performances["portfolio_twr"]),
                "portfolio_gain": self.convert_df_to_json(performances["portfolio_gain"]),
                "portfolio_monthly_percentages": self.convert_data_monthly_percentage_to_json(
                    performances["portfolio_monthly_percentages"]
                ),
                "portfolio_valuation": self.convert_df_to_json(performances["portfolio_valuation"]),
                "portfolio_invested_amounts": self.convert_df_to_json(performances["portfolio_invested_amounts"]),
                "portfolio_cash": self.convert_df_to_json(performances["portfolio_cash"]),
                "portfolio_fees": self.convert_df_to_json(performances["portfolio_fees"]),
                "portfolio_cagr": performances["portfolio_cagr"],
                "portfolio_dividend_yield": performances["portfolio_dividend_yield"],
                "portfolio_dividend_earn": performances["portfolio_dividend_earn"],
            }
        )

    @staticmethod
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

    def get_twr(self):
        return {"portfolio_twr": self.convert_df_to_json(self.performances["portfolio_twr"])}
