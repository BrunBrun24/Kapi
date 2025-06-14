import numpy as np
import pandas as pd
from datetime import datetime
from api.models import PortfolioTransaction, PortfolioTicker, PortfolioPerformance, Portfolio
from api.services.modules.portfolios.my_portfolio import MyPortfolio
from api.services.modules.recuperation_donnees import DataRetrieval
from django.contrib.auth import get_user_model

from api.services.modules.portfolios.dollar_cost_averaging import DollarCostAveraging

class PortefeuilleBourse(DataRetrieval, MyPortfolio, DollarCostAveraging):
    def __init__(self, user_id: int, portfolio_id: int):
        self.user_id = user_id
        self.portfolio_id = portfolio_id
        name_portfolio = Portfolio.objects.filter(id=portfolio_id).values("name").first()["name"]
        
        # Récupère les transactions avec les IDs de PortfolioTicker
        transactions = PortfolioTransaction.objects.filter(
            user=user_id,
            portfolio=portfolio_id,
        ).values(
            'id',
            'portfolio_ticker_id',
            'operation',
            'date',
            'amount',
            'fees',
            'stock_price',
            'quantity',
            'currency'
        ).order_by("date")

        # Convertit en DataFrame
        transactions_df = pd.DataFrame(transactions)

        if (transactions_df.empty) or (transactions_df[transactions_df['operation'] == 'buy'].empty):
            self.save_portfolio_empty()
            return

        # Convertit les colonnes numériques en float
        numeric_columns = ['amount', 'fees', 'stock_price', 'quantity']
        transactions_df[numeric_columns] = transactions_df[numeric_columns].astype(float)

        # Conversion explicite de la date et mise en index
        transactions_df['date'] = pd.to_datetime(transactions_df['date'])
        transactions_df.set_index('date', inplace=True)

        # Mapping ticker depuis PortfolioTicker
        ticker_mapping = {
            pt.id: pt.ticker.ticker
            for pt in PortfolioTicker.objects.filter(
                id__in=transactions_df['portfolio_ticker_id'].dropna().unique()
            ).select_related('ticker')
        }

        # Ajoute la colonne 'ticker'
        transactions_df['ticker'] = transactions_df['portfolio_ticker_id'].map(ticker_mapping)

        self.transactions = transactions_df

        self.start_date = transactions_df.index[0]
        self.end_date = datetime.today()

        self.tickers_invested_amounts = {}  # Montants investis par action
        self.tickers_sold_amounts = {}  # Montants obtenus lors des ventes
        self.ticker_twr = {}  # Time-Weighted Return par action
        self.tickers_net_prices = {}  # Prix net des actions
        self.tickers_gross_prices = {}  # Prix brut des actions
        self.tickers_funds_invested = {}  # Fonds investis par action
        self.tickers_dividends = {}

        self.portfolio_twr = pd.DataFrame(dtype=float)  # Performance pondérée dans le temps du portefeuille
        self.portfolio_net_price = pd.DataFrame(dtype=float)  # Prix net du portefeuille
        self.portfolio_monthly_percentages = pd.DataFrame(dtype=float)  # Pourcentages mensuels du portefeuille
        self.bank_balance = pd.DataFrame(dtype=float)  # Solde du compte bancaire
        self.cash = pd.DataFrame(dtype=float)  # Cash disponible
        self.total_invested_amounts = pd.DataFrame(dtype=float)  # Évolution des montants investis

        self.my_portfolio(name_portfolio)

        portfolioPercentage = [
            [{'CSSPX.MI': 100}, 'S&P 500']
        ]
        self.set_portfolio_allocation(portfolioPercentage)
        self.dca()
        
        self.save_portfolio_performance()

    ################ A SUPPRIMER ################
    def add_global_porfolio(self):
        global_portfolio = Portfolio.objects.filter(user_id=self.user_id, name="My Portfolio").values().first()
        name_portfolio = global_portfolio["name"]
        
        # Récupère les transactions avec les IDs de PortfolioTicker
        transactions = PortfolioTransaction.objects.filter(
            user=self.user_id,
            portfolio=global_portfolio["id"],
        ).values(
            'id',
            'portfolio_ticker_id',
            'operation',
            'date',
            'amount',
            'fees',
            'stock_price',
            'quantity',
            'currency'
        ).order_by("date")

        # Convertit en DataFrame
        transactions_df = pd.DataFrame(transactions)

        if (transactions_df.empty) or (transactions_df[transactions_df['operation'] == 'buy'].empty):
            self.save_portfolio_empty()
            return

        # Convertit les colonnes numériques en float
        numeric_columns = ['amount', 'fees', 'stock_price', 'quantity']
        transactions_df[numeric_columns] = transactions_df[numeric_columns].astype(float)

        # Conversion explicite de la date et mise en index
        transactions_df['date'] = pd.to_datetime(transactions_df['date'])
        transactions_df.set_index('date', inplace=True)

        # Mapping ticker depuis PortfolioTicker
        ticker_mapping = {
            pt.id: pt.ticker.ticker
            for pt in PortfolioTicker.objects.filter(
                id__in=transactions_df['portfolio_ticker_id'].dropna().unique()
            ).select_related('ticker')
        }

        # Ajoute la colonne 'ticker'
        transactions_df['ticker'] = transactions_df['portfolio_ticker_id'].map(ticker_mapping)

        self.transactions = transactions_df
        self.start_date = transactions_df.index[0]

        self.my_portfolio(name_portfolio)


    def set_portfolio_allocation(self, portfolio_allocation: list):
        """
        Définit l'allocation du portefeuille avec les pourcentages pour chaque actif.

        Args:
            portfolio_allocation (list): Liste contenant des allocations de portefeuille.
                Chaque élément est une liste composée de :
                - Un dictionnaire avec les tickers comme clés et les pourcentages comme valeurs.
                - Une chaîne représentant le nom du portefeuille.
        """
        assert isinstance(portfolio_allocation, list), "portfolio_allocation doit être une liste de portefeuilles."
        for portfolio in portfolio_allocation:
            assert isinstance(portfolio, list) and len(portfolio) == 2, \
                "Chaque portefeuille doit être une liste contenant un dictionnaire et une chaîne de caractères."
            assert isinstance(portfolio[0], dict), "Le premier élément doit être un dictionnaire des actions avec leurs pourcentages."
            assert isinstance(portfolio[1], str), "Le deuxième élément doit être une chaîne représentant le nom du portefeuille."
            for ticker, percentage in portfolio[0].items():
                assert isinstance(ticker, str), f"Chaque clé (ticker) doit être une chaîne, mais '{ticker}' ne l'est pas."
                assert isinstance(percentage, (int, float)), f"Chaque valeur (pourcentage) doit être un nombre, mais '{percentage}' ne l'est pas."

        self.portfolio_allocation = portfolio_allocation

        all_tickers = sorted(set([ticker for portfolio in self.portfolio_allocation for ticker in portfolio[0].keys()]))
        initial_tickers = sorted(list(self.tickers_prices.columns))
        new_tickers = [ticker for ticker in all_tickers if ticker not in initial_tickers]

        new_tickers_prices = self.download_tickers_price(new_tickers, self.start_date, self.end_date)
        self.tickers_prices = pd.concat([self.tickers_prices, new_tickers_prices], axis=1)

    @staticmethod
    def dataframe_to_clean_json_dict(dataframes_dict):
        result = {}
        for key, df in dataframes_dict.items():
            # On s'assure que l'index est une date en string ISO
            df = df.copy()
            df.index = df.index.astype(str)

            # Remplacer tous les NaN/NaT/inf par None
            df_clean = df.replace([np.nan, np.inf, -np.inf], None)

            # Conversion en dict
            result[key] = df_clean.to_dict(orient="index")
        return result

    @staticmethod
    def dataframe_to_json_compatible(df: pd.DataFrame) -> dict:
        """
        Convertit un DataFrame en un dict JSON-compatible.
        L'index est converti en chaînes ISO, les valeurs en float/int ou null.
        """
        df_clean = df.copy()

        # Forcer l'index en string (format ISO recommandé)
        df_clean.index = df_clean.index.map(lambda x: x.isoformat() if isinstance(x, pd.Timestamp) else str(x))

        # Nettoyage des NaN/inf
        df_clean = df_clean.round(6).astype(object).where(pd.notnull(df_clean), None)

        return df_clean.to_dict(orient="index")


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


    def save_portfolio_performance(self):
        User = get_user_model()
        user_instance = User.objects.get(id=self.user_id)
        portfolio_instance = Portfolio.objects.get(id=self.portfolio_id)

        PortfolioPerformance.objects.update_or_create(
        user=user_instance,
        portfolio=portfolio_instance,
        defaults={
            "twr_by_ticker": self.convert_data_to_json(self.ticker_twr),
            "net_price_by_ticker": self.convert_data_to_json(self.tickers_net_prices),
            "gross_price_by_ticker": self.convert_data_to_json(self.tickers_gross_prices),
            "invested_by_ticker": self.convert_data_to_json(self.tickers_funds_invested),
            "sold_by_ticker": self.convert_data_to_json(self.tickers_sold_amounts),
            "dividends_by_ticker": self.convert_data_to_json(self.tickers_dividends),

            "portfolio_twr": self.convert_df_to_json(self.portfolio_twr),
            "net_portfolio_price": self.convert_df_to_json(self.portfolio_net_price),
            "monthly_percentage": self.convert_df_to_json(self.portfolio_monthly_percentages),
            "bank_balance": self.convert_df_to_json(self.bank_balance),
            "total_invested": self.convert_df_to_json(self.total_invested_amounts),
            "cash": self.convert_df_to_json(self.cash),
        }
    )

    def save_portfolio_empty(self):
        User = get_user_model()
        user_instance = User.objects.get(id=self.user_id)
        portfolio_instance = Portfolio.objects.get(id=self.portfolio_id)

        PortfolioPerformance.objects.update_or_create(
        user=user_instance,
        portfolio=portfolio_instance,
        defaults={
            "twr_by_ticker": {},
            "net_price_by_ticker": {},
            "gross_price_by_ticker": {},
            "invested_by_ticker": {},
            "sold_by_ticker": {},
            "dividends_by_ticker": {},
            "portfolio_twr": {},
            "net_portfolio_price": {},
            "monthly_percentage": {},
            "bank_balance": {},
            "total_invested": {},
            "cash": {},
        }
    )
