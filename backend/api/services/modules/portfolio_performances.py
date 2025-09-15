from collections import defaultdict
import pandas as pd
from datetime import datetime
from api.models import PortfolioTransaction, PortfolioTicker, PortfolioPerformance, Portfolio, StockPrice
from api.services.modules.portfolios.my_portfolio import MyPortfolio
from django.contrib.auth import get_user_model

from api.services.modules.portfolios.dollar_cost_averaging import DollarCostAveraging
from api.services.modules.portfolios.replication import Replication
from api.services.modules.portfolios.base_portfolio import BasePortfolio

class PorfolioPerformances(MyPortfolio, DollarCostAveraging, Replication):
    def __init__(self, user, portfolios, start_date: datetime = None, tickers_valuations: dict = {}):
        self.user = user
        self.tickers_valuations = tickers_valuations
        self.performances = self._init_performance_structure()

        # Normalise la liste de portefeuilles
        self.portfolios = self._normalize_portfolios(portfolios)

        # Récupère les tickers et prix d’ouverture globaux
        self.tickers_open_prices = self._load_all_open_prices()
        self.end_date = pd.to_datetime(self.tickers_open_prices.index[-1])

        # Lance le traitement pour chaque portefeuille
        for portfolio in self.portfolios:
            self._process_portfolio(portfolio, start_date)

    def _init_performance_structure(self) -> dict:
        """Initialise la structure des performances du portefeuille."""
        return {
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

    def _normalize_portfolios(self, portfolios):
        """Convertit en liste de portefeuilles selon le type fourni (int, objet ou liste)."""
        if isinstance(portfolios, int):
            return Portfolio.objects.filter(pk=portfolios, user=self.user)
        elif isinstance(portfolios, Portfolio):
            return [portfolios]
        return portfolios

    def _load_all_open_prices(self) -> pd.DataFrame:
        """Charge les prix d’ouverture pour tous les tickers utilisés par les utilisateurs."""
        tickers = PortfolioTicker.get_all_unique_tickers()
        return StockPrice.get_open_prices_dataframe_for_tickers(tickers)

    def _process_portfolio(self, portfolio, start_date):
        """Traite un portefeuille utilisateur complet : transactions, performances, benchmarks."""
        performances_tickers_eur = self._init_tickers_structure()
        currencies_tickers = PortfolioTicker.get_user_tickers_by_currency(
            user_id=self.user.id, portfolio_id=portfolio.id
        )

        transactions_not_empty = self._process_currencies(
            portfolio, currencies_tickers, performances_tickers_eur, start_date
        )

        if transactions_not_empty:
            self._compute_portfolio_results(portfolio, performances_tickers_eur, start_date)
        else:
            if start_date is None:
                self._save_portfolio_performance_empty()

    def _init_tickers_structure(self) -> dict:
        """Initialise la structure des performances par ticker."""
        return {
            "tickers_invested_amounts": {},
            "tickers_twr": {},
            "tickers_gain": {},
            "tickers_valuation": {},
            "tickers_dividends": {},
            "tickers_pru": {},
        }

    def _process_currencies(self, portfolio, currencies_tickers, performances_tickers_eur, start_date) -> bool:
        """Traite toutes les devises d’un portefeuille."""
        transactions_not_empty = False
        for currency, tickers in currencies_tickers.items():
            transactions = PortfolioTransaction.get_transactions_dataframe(
                user=self.user.id, portfolio=portfolio.id, currency=currency
            )

            if start_date is not None:
                transactions = self._set_transaction_with_date(
                    transactions,
                    start_date,
                    self.tickers_valuations,
                    StockPrice.convert_dataframe_to_currency(self.tickers_open_prices, currency)
                )
            else:
                start_date = pd.to_datetime(transactions.index[0]).normalize()

            if not transactions.empty:
                transactions_not_empty = True
                self._process_transactions(portfolio, transactions, tickers, currency, performances_tickers_eur, start_date)
        return transactions_not_empty

    def _process_transactions(self, portfolio, transactions, tickers, currency, performances_tickers_eur, start_date):
        """Calcule et sauvegarde les performances pour une devise donnée."""
        portfolio_name = Portfolio.get_user_portfolio_name(self.user.id, portfolio.id)

        tickers_open_prices_currency = self._prepare_open_prices_currency(tickers, currency, start_date)
        results = self.my_portfolio(transactions=transactions, tickers_prices=tickers_open_prices_currency, start_date=start_date, end_date=self.end_date)

        self._save_performance_tickers(self.performances, results, portfolio_name)

        if currency == "EUR":
            self._save_performance_tickers(performances_tickers_eur, results, portfolio_name)
        elif currency == "USD":
            for key, df in results.items():
                if key != "tickers_twr":
                    StockPrice.convert_dataframe_to_currency(df, "EUR")
            self._save_performance_tickers(performances_tickers_eur, results, portfolio_name)

    def _prepare_open_prices_currency(self, tickers, currency, start_date):
        """Prépare le dataframe des prix d’ouverture filtré et converti pour une devise donnée."""
        tickers_open_prices_currency = self.tickers_open_prices.loc[:, self.tickers_open_prices.columns.intersection(tickers)]
        tickers_open_prices_currency = StockPrice.convert_dataframe_to_currency(tickers_open_prices_currency, currency)
        tickers_open_prices_currency = tickers_open_prices_currency.loc[start_date:]
        all_dates = pd.date_range(start=start_date, end=self.end_date, freq='D')
        return tickers_open_prices_currency.reindex(all_dates).ffill().bfill()
    
    def _compute_portfolio_results(self, portfolio, performances_tickers_eur, start_date):
        """Calcule les performances globales du portefeuille et effectue la comparaison avec les benchmarks."""
        # Nom du portefeuille
        portfolio_name = Portfolio.get_user_portfolio_name(self.user.id, portfolio.id)

        # Dates de début/fin
        if start_date is None:
            start_date, _ = PortfolioTransaction.first_and_last_date(self.user.id, portfolio.id)

        # Performances consolidées en EUR
        portfolio_valuation = performances_tickers_eur["tickers_valuation"][portfolio_name].sum(axis=1)
        portfolio_invested_amounts = performances_tickers_eur["tickers_invested_amounts"][portfolio_name].sum(axis=1)

        # Transactions converties en EUR
        transactions_eur = PortfolioTransaction.get_transactions_in_eur(self.user.id, portfolio.id)
        if start_date is not None:
            transactions_eur = self._set_transaction_with_date(
                transactions_eur,
                start_date,
                self.tickers_valuations,
                StockPrice.convert_dataframe_to_currency(self.tickers_open_prices, "EUR")
            )

        base_portfolio = BasePortfolio(start_date, self.end_date)

        # Plus-values réalisées
        portfolio_realized_gains_losses = base_portfolio.compute_plus_value_evolution(
            transactions_eur,
            performances_tickers_eur["tickers_invested_amounts"][portfolio_name]
        )["plus_value_cumulative"]

        # Gain total = gain latent + plus-values réalisées
        portfolio_gain = performances_tickers_eur["tickers_gain"][portfolio_name].sum(axis=1) + portfolio_realized_gains_losses

        # Argent investi (hors plus-values réalisées)
        invested_money = (
            performances_tickers_eur["tickers_invested_amounts"][portfolio_name].sum(axis=1).iloc[-1] - portfolio_realized_gains_losses.iloc[-1]
        )

        # % de gain
        portfolio_gain_pct = base_portfolio.calculate_portfolio_percentage_change(portfolio_gain, invested_money)

        # Sauvegarde des résultats globaux
        self.performances["portfolio_valuation"][portfolio_name] = portfolio_valuation
        self.performances["portfolio_invested_amounts"][portfolio_name] = portfolio_invested_amounts
        self.performances["portfolio_gain"][portfolio_name] = portfolio_gain
        self.performances["portfolio_twr"][portfolio_name] = portfolio_gain_pct
        self.performances["portfolio_monthly_percentages"][portfolio_name] = base_portfolio.calculate_monthly_percentage_change(
            portfolio_valuation, transactions_eur
        )
        self.performances["portfolio_dividend_earn"][portfolio_name] = base_portfolio.calculate_dividend_earn(transactions_eur)
        self.performances["portfolio_dividend_yield"][portfolio_name] = base_portfolio.calculate_dividend_yield(
            transactions_eur, portfolio_valuation
        )
        self.performances["portfolio_cash"][portfolio_name] = base_portfolio.compute_cash_evolution(transactions_eur)["cash_cumulative"]
        self.performances["portfolio_fees"][portfolio_name] = base_portfolio.compute_fees_evolution(transactions_eur)["cumulative_fees"]
        self.performances["portfolio_cagr"][portfolio_name] = base_portfolio.calculate_portfolio_cagr(portfolio_valuation, portfolio_invested_amounts)

        # -------------------------
        # Benchmarks
        # -------------------------
        portfolios_allocation = [
            [{'CSSPX.MI': 100}, 'S&P 500'],
            [{'NQ=F': 100}, 'Nasdaq 100'],
            [{'URTH': 100}, 'MSCI WORLD'],
            [{'^FCHI': 100}, 'CAC 40'],
        ]

        tickers_portfolio_allocation = sorted(set([ticker for portfolio in portfolios_allocation for ticker in portfolio[0].keys()]))

        # Colonnes déjà présentes
        existing_tickers = [t for t in tickers_portfolio_allocation if t in self.tickers_open_prices.columns]
        # Colonnes manquantes
        missing_tickers = [t for t in tickers_portfolio_allocation if t not in self.tickers_open_prices.columns]

        df_existing = self.tickers_open_prices[existing_tickers].copy() if existing_tickers else pd.DataFrame()
        df_missing = StockPrice.get_open_prices_dataframe_for_tickers(missing_tickers) if missing_tickers else pd.DataFrame()

        # Fusion des prix
        benchmarks_prices = pd.concat([df_existing, df_missing], axis=1)
        benchmarks_prices = benchmarks_prices[tickers_portfolio_allocation]
        benchmarks_prices = StockPrice.convert_dataframe_to_currency(benchmarks_prices, "EUR")

        # Argent de départ (argent investi réellement dans le portefeuille)
        money = base_portfolio.initial_invested_amount(
            transactions_eur,
            performances_tickers_eur["tickers_invested_amounts"][portfolio_name]
        )

        # Calcul pour chaque benchmark
        for portfolio_allocation in portfolios_allocation:
            benchmarks_performances = self.dca(portfolio_allocation, benchmarks_prices, money, start_date, self.end_date)
            self.save_performance_benchmarks(self.performances, benchmarks_performances, portfolio_allocation[-1])

        # Si pas de start_date (cas "réel"), on enregistre en base
        if start_date is None:
            self._save_portfolio_performance(self.user, portfolio, self.performances)



    def _set_transaction_with_date(self, transactions_all: pd.DataFrame, start_date: datetime, tickers_valuations: dict, tickers_prices: pd.DataFrame) -> pd.DataFrame:
        """
        Ajoute des transactions fictives 'buy' à une date donnée pour représenter
        une valorisation initiale du portefeuille.

        :param transactions_all: DataFrame contenant toutes les transactions
        :param start_date: date de départ des transactions
        :param tickers_valuations: dictionnaire {ticker: montant_en_euros}
        :param tickers_prices: DataFrame des prix par ticker (index = dates)
        """
        start_date = pd.to_datetime(start_date).normalize()
        tickers_prices.index = pd.to_datetime(tickers_prices.index).normalize()
        tickers_prices = tickers_prices.ffill().bfill()

        # Prendre la date la plus proche disponible
        start_date = tickers_prices.index[
            tickers_prices.index.get_indexer([start_date], method='nearest')[0]
        ]
        start_date = start_date

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

    @staticmethod
    def _save_performance_tickers(all_performance: dict, performance: pd.DataFrame, portfolio_name: str):
        """
        Sauvegarde ou met à jour les performances par ticker pour un portefeuille donné.

        :param all_performance: dictionnaire global contenant toutes les performances
        :param performance: DataFrame avec les performances calculées
        :param portfolio_name: nom du portefeuille
        """
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
        """
        Sauvegarde ou met à jour les performances des benchmarks pour un portefeuille donné.

        :param all_performance: dictionnaire global contenant toutes les performances
        :param performance: DataFrame avec les performances calculées
        :param portfolio_name: nom du portefeuille
        """
        for key in (
            "tickers_invested_amounts",
            "tickers_twr",
            "tickers_gain",
            "tickers_valuation",
            "tickers_dividends",
            "tickers_pru",
        ):
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
            "portfolio_dividend_earn",
        }:
            all_performance[key][portfolio_name] = performance[key]

    @staticmethod
    def _convert_df_to_json(df: pd.DataFrame):
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

    def _convert_data_to_json(self, data: dict):
        """
        Convertit un dictionnaire de DataFrames en liste de listes prête pour JSON.

        :param data: dictionnaire {nom_portefeuille: DataFrame}
        """
        return [[portfolio, self._convert_df_to_json(df)] for portfolio, df in data.items()]

    @staticmethod
    def _convert_data_monthly_percentage_to_json(df: pd.DataFrame):
        """
        Convertit un DataFrame en dictionnaire structuré par ticker / année / mois.

        :param df: DataFrame avec index datetime et colonnes représentant des tickers
        """
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

    def _save_portfolio_performance(self, user, portfolio, performances: dict):
        """
        Enregistre ou met à jour les performances d'un portefeuille dans la base de données.

        :param user: instance de l'utilisateur
        :param portfolio: instance du portefeuille
        :param performances: dictionnaire contenant toutes les performances calculées
        """
        User = get_user_model()
        user_instance = User.objects.get(id=user.id)
        portfolio_instance = Portfolio.objects.get(id=portfolio.id)

        PortfolioPerformance.objects.update_or_create(
            user=user_instance,
            portfolio=portfolio_instance,
            defaults={
                "tickers_invested_amounts": self._convert_data_to_json(performances["tickers_invested_amounts"]),
                "tickers_twr": self._convert_data_to_json(performances["tickers_twr"]),
                "tickers_gain": self._convert_data_to_json(performances["tickers_gain"]),
                "tickers_valuation": self._convert_data_to_json(performances["tickers_valuation"]),
                "tickers_dividends": self._convert_data_to_json(performances["tickers_dividends"]),
                "tickers_pru": self._convert_data_to_json(performances["tickers_pru"]),
                "portfolio_twr": self._convert_df_to_json(performances["portfolio_twr"]),
                "portfolio_gain": self._convert_df_to_json(performances["portfolio_gain"]),
                "portfolio_monthly_percentages": self._convert_data_monthly_percentage_to_json(
                    performances["portfolio_monthly_percentages"]
                ),
                "portfolio_valuation": self._convert_df_to_json(performances["portfolio_valuation"]),
                "portfolio_invested_amounts": self._convert_df_to_json(performances["portfolio_invested_amounts"]),
                "portfolio_cash": self._convert_df_to_json(performances["portfolio_cash"]),
                "portfolio_fees": self._convert_df_to_json(performances["portfolio_fees"]),
                "portfolio_cagr": performances["portfolio_cagr"],
                "portfolio_dividend_yield": performances["portfolio_dividend_yield"],
                "portfolio_dividend_earn": performances["portfolio_dividend_earn"],
            }
        )

    @staticmethod
    def _save_portfolio_performance_empty(user, portfolio):
        """
        Crée ou met à jour un enregistrement vide de performances pour un portefeuille
        n'ayant aucune transaction.

        :param user: instance de l'utilisateur
        :param portfolio: instance du portefeuille
        """
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
        return {"portfolio_twr": self._convert_df_to_json(self.performances["portfolio_twr"])}
