from collections import defaultdict
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from api.models import PortfolioTransaction, PortfolioTicker, PortfolioPerformance, Portfolio
from api.services.modules.portfolios.my_portfolio import MyPortfolio
from django.contrib.auth import get_user_model
import yfinance as yf
from concurrent.futures import ThreadPoolExecutor, as_completed

from api.services.modules.portfolios.dollar_cost_averaging import DollarCostAveraging
from api.services.modules.portfolios.replication import Replication

class PortefeuilleBourse(MyPortfolio, DollarCostAveraging, Replication):
    def __init__(self, user_id: int, portfolio_id: int, start_date: datetime = None, tickers_valuations: dict = {}):
        self.user_id = user_id
        self.portfolio_id = portfolio_id
        portfolio_name  = Portfolio.objects.filter(id=portfolio_id).values("name").first()["name"]
        
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
        # Ajuster les quantités en fonction des splits
        self.ajuster_quantites_splits(transactions_df)

        self.transactions = transactions_df

        self.start_date = transactions_df.index[0]
        self.end_date = datetime.today()

        self.tickers_invested_amounts = {}
        self.tickers_sold_amounts = {}
        self.tickers_twr = {}
        self.tickers_gain = {}
        self.tickers_valuation = {}
        self.ticker_invested_amounts = {}
        self.tickers_dividends = {}
        self.tickers_pru = {}

        self.portfolio_twr = pd.DataFrame(dtype=float)
        self.portfolio_gain = pd.DataFrame(dtype=float)
        self.portfolio_monthly_percentages = pd.DataFrame(dtype=float)
        self.portfolio_valuation = pd.DataFrame(dtype=float)
        self.portfolio_invested_amounts = pd.DataFrame(dtype=float)
        self.portfolio_cash = pd.DataFrame(dtype=float)

        self.portfolio_fees = pd.DataFrame(dtype=float)
        self.portfolio_cagr = {}
        self.portfolio_dividend_yield = {}
        self.portfolio_dividend_earn = {}

        if start_date is not None:
            self.transactions = self.set_transaction_with_date(transactions_df, start_date, tickers_valuations)
            self.start_date = self.transactions.index[0]
            
        self.my_portfolio(portfolio_name)

        portfolio_percentage = [
            [{'SPY': 100}, 'S&P 500'],
            [{'NQ=F': 100}, 'Nasdaq 100'],
            [{'URTH': 100}, 'MSCI WORLD'],
            [{'^FCHI': 100}, 'CAC 40'],
        ]
        self.set_portfolio_allocation(portfolio_percentage)
        self.dca()

        if start_date is None:
            self.save_portfolio_performance()

    @staticmethod
    def ajuster_quantites_splits(transactions_df: pd.DataFrame) -> pd.DataFrame:
        """
        Ajuste les colonnes 'quantity' et 'stock_price' d'un DataFrame de transactions
        en fonction des splits ayant eu lieu après chaque transaction.

        :param transactions_df: DataFrame contenant une colonne 'ticker', 'quantity', 'stock_price' et un index datetime
        :return: DataFrame avec les colonnes 'quantity' et 'stock_price'
        """
        
        def get_splits(ticker):
            try:
                splits = yf.Ticker(ticker).splits
                return ticker, splits.tz_convert(None) if not splits.empty else None
            except Exception as e:
                print(f"Erreur lors de la récupération des splits pour {ticker} : {e}")
                return ticker, None

        # Supprimer les lignes sans ticker et obtenir les tickers uniques
        unique_tickers = transactions_df['ticker'].dropna().unique()

        # Utiliser un ThreadPool pour paralléliser les appels à yfinance
        splits_dict = {}
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(get_splits, ticker): ticker for ticker in unique_tickers}
            for future in as_completed(futures):
                ticker, splits = future.result()
                if splits is not None:
                    splits_dict[ticker] = splits

        # Fonction d'ajustement pour une seule ligne
        def ajuster_ligne(row):
            ticker = row['ticker']
            date_transaction = row.name
            quantite_initiale = row['quantity']
            prix_initial = row['stock_price']

            if ticker not in splits_dict:
                return pd.Series({
                    'quantity': quantite_initiale,
                    'stock_price': prix_initial
                })

            splits_ticker = splits_dict[ticker]
            splits_apres = splits_ticker[splits_ticker.index > date_transaction]

            facteur_split = splits_apres.prod() if not splits_apres.empty else 1.0

            return pd.Series({
                'quantity': quantite_initiale * facteur_split,
                'stock_price': prix_initial / facteur_split
            })

        # Appliquer les ajustements
        ajustements = transactions_df.apply(
            lambda row: ajuster_ligne(row) if pd.notna(row['ticker']) else pd.Series({
                'quantity': row['quantity'],
                'stock_price': row['stock_price']
            }),
            axis=1
        )

        # Fusionner les résultats dans le DataFrame original
        transactions_df['quantity'] = ajustements['quantity']
        transactions_df['stock_price'] = ajustements['stock_price']

        return transactions_df

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

        all_tickers = sorted(set([ticker for portfolio in portfolio_allocation for ticker in portfolio[0].keys()]))
        initial_tickers = sorted(list(self.tickers_prices.columns))
        new_tickers = [ticker for ticker in all_tickers if ticker not in initial_tickers]

        new_tickers_prices = self.download_tickers_price(new_tickers, self.start_date, self.end_date)
        self.tickers_prices = pd.concat([self.tickers_prices, new_tickers_prices], axis=1)

    @staticmethod
    def set_transaction_with_date(transactions_df: pd.DataFrame, start_date: datetime, tickers_valuations: dict) -> pd.DataFrame:
        # S'assurer que l'index est bien de type datetime
        if not isinstance(transactions_df.index, pd.DatetimeIndex):
            transactions_df.index = pd.to_datetime(transactions_df.index)

        # Filtrer les transactions à partir de la date de départ
        transactions_df = transactions_df[transactions_df.index >= start_date]

        new_rows = []

        for ticker, valuation in tickers_valuations.items():
            date_lookup = start_date - timedelta(days=1)
            date_str = date_lookup.strftime('%Y-%m-%d')

            try:
                data = yf.download(ticker, start=date_str, end=start_date.strftime('%Y-%m-%d'), auto_adjust=True, progress=False)
                if data.empty:
                    print(f"Aucune donnée trouvée pour {ticker} à la date {date_str}")
                    continue

                stock_price = data['Close'].iloc[0].item()
                quantity = float(valuation) / stock_price

                new_row = {
                    'id': None,
                    'portfolio_ticker_id': None,
                    'operation': 'buy',
                    'amount': float(valuation),
                    'fees': 0.0,
                    'stock_price': stock_price,
                    'quantity': quantity,
                    'currency': None,
                    'ticker': ticker
                }

                new_rows.append((start_date, new_row))

            except Exception as e:
                print(f"Erreur lors du traitement du ticker {ticker}: {e}")

        # Créer un DataFrame avec les mêmes colonnes que transactions_df
        if new_rows:
            new_df = pd.DataFrame(
                [row for _, row in new_rows],
                index=[date for date, _ in new_rows],
                columns=transactions_df.columns  # Assure la même structure
            )
            new_df.index.name = 'date'

            # Supprimer les colonnes entièrement vides pour éviter les warnings
            new_df = new_df.dropna(axis=1, how='all')

            # Fusionner et trier
            transactions_df = pd.concat([new_df, transactions_df]).sort_index()

        # Trier le DataFrame final par ordre chronologique sur l'index (qui contient les dates)
        transactions_df = transactions_df.sort_index()

        return transactions_df

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

    def save_portfolio_performance(self):
        User = get_user_model()
        user_instance = User.objects.get(id=self.user_id)
        portfolio_instance = Portfolio.objects.get(id=self.portfolio_id)

        PortfolioPerformance.objects.update_or_create(
        user=user_instance,
        portfolio=portfolio_instance,
        defaults={
            "tickers_invested_amounts": self.convert_data_to_json(self.tickers_invested_amounts),
            "tickers_sold_amounts": self.convert_data_to_json(self.tickers_sold_amounts),
            "tickers_twr": self.convert_data_to_json(self.tickers_twr),
            "tickers_gain": self.convert_data_to_json(self.tickers_gain),
            "tickers_valuation": self.convert_data_to_json(self.tickers_valuation),
            "ticker_invested_amounts": self.convert_data_to_json(self.ticker_invested_amounts),
            "tickers_dividends": self.convert_data_to_json(self.tickers_dividends),
            "tickers_pru": self.convert_data_to_json(self.tickers_pru),

            "portfolio_twr": self.convert_df_to_json(self.portfolio_twr),
            "portfolio_gain": self.convert_df_to_json(self.portfolio_gain),
            "portfolio_monthly_percentages": self.convert_data_monthly_percentage_to_json(self.portfolio_monthly_percentages),
            "portfolio_valuation": self.convert_df_to_json(self.portfolio_valuation),
            "portfolio_invested_amounts": self.convert_df_to_json(self.portfolio_invested_amounts),
            "portfolio_cash": self.convert_df_to_json(self.portfolio_cash),
            "portfolio_fees": self.convert_df_to_json(self.portfolio_fees),

            "portfolio_cagr": self.portfolio_cagr,
            "portfolio_dividend_yield": self.portfolio_dividend_yield,
            "portfolio_dividend_earn": self.portfolio_dividend_earn,
        }
    )

    def save_portfolio_empty(self):
        User = get_user_model()
        user_instance = User.objects.get(id=self.user_id)
        portfolio_instance = Portfolio.objects.get(id=self.portfolio_id)

        PortfolioPerformance.objects.update_or_create(
        user=user_instance,
        portfolio=portfolio_instance,
        defaults = {
            "tickers_invested_amounts": {},
            "tickers_sold_amounts": {},
            "tickers_twr": {},
            "tickers_gain": {},
            "tickers_valuation": {},
            "ticker_invested_amounts": {},
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

    def get_twr(self) -> list:
        return self.convert_df_to_json(self.portfolio_twr)
    
