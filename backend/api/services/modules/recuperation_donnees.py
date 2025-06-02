import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta


class DataRetrieval:
    """
    Cette classe permet de récupérer toutes les données nécessaires pour l'analyse. 
    Elle télécharge les données à partir d'Internet.
    """

    def download_tickers_price(self, tickers: list, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """
        Télécharge les prix de clôture des actions spécifiées sur une période donnée.

        Args:
            tickers (list): Liste des symboles boursiers à télécharger.
            start_date (datetime): Date de début du téléchargement.
            end_date (datetime): Date de fin du téléchargement.

        Returns:
            pd.DataFrame: Un DataFrame contenant les prix de clôture des actions spécifiées,
            avec les dates manquantes complétées et les prix éventuellement convertis en EUR.
        """
        assert isinstance(tickers, list) and all(isinstance(ticker, str) for ticker in tickers), "tickers doit être une liste de chaînes de caractères"
        assert isinstance(start_date, datetime), "start_date doit être un objet datetime"
        assert isinstance(end_date, datetime), "end_date doit être un objet datetime"

        # Téléchargement des données pour plusieurs tickers ou un seul
        if len(tickers) > 1:
            ticker_prices = yf.download(tickers, start=start_date, end=end_date, interval="1d", auto_adjust=True)["Close"].ffill().bfill()
        else:
            ticker_prices = pd.DataFrame()
            for symbol in tickers:
                ticker_prices[symbol] = yf.download(symbol, start=start_date, end=end_date, interval="1d", auto_adjust=True)["Close"].ffill().bfill()

        # Gérer les dates manquantes dans ticker_prices
        all_dates = pd.date_range(start=start_date, end=end_date, freq='D')
        ticker_prices = ticker_prices.reindex(all_dates).ffill().bfill()

        return self.convert_currency_usd_to_eur(ticker_prices, start_date, end_date)

    @staticmethod
    def convert_currency_usd_to_eur(df: pd.DataFrame, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """
        Convertit les valeurs d'un DataFrame d'une devise à une autre sur une période spécifiée.

        Args:
            df (pd.DataFrame): DataFrame contenant les données financières en différentes devises.
            start_date (datetime): Date de début.
            end_date (datetime): Date de fin'.

        Returns:
            pd.DataFrame: Un DataFrame avec les valeurs converties en utilisant le taux de change correspondant.
        """
        assert isinstance(df, pd.DataFrame), f"df doit être un DataFrame: ({type(df)})"
        assert isinstance(start_date, datetime), f"start_date doit être un objet datetime: ({type(start_date)})"
        assert isinstance(end_date, datetime), f"end_date doit être un objet datetime: ({type(end_date)})"
        assert all(df.dtypes == 'float64') or all(df.dtypes == 'int64'), "Les colonnes du DataFrame doivent contenir des valeurs numériques."

        # Télécharger les données de la devise
        conversion_rate_df = yf.download("EURUSD=X", start=start_date, end=end_date, interval="1d", auto_adjust=True)["Close"]

        # Gérer les dates manquantes dans conversion_rate_df
        all_dates = pd.date_range(start=start_date, end=end_date, freq='D')
        conversion_rate_df = conversion_rate_df.reindex(all_dates).ffill().bfill()

        # Filtrer les colonnes de df pour ne garder que celles qui doivent être converties
        tickers_to_convert = [ticker for ticker in df.columns if "." not in ticker]
        df_filtered = df.loc[:, df.columns.intersection(tickers_to_convert)]

        # Aligner et diviser les valeurs pour la conversion
        df_filtered = df_filtered.divide(conversion_rate_df["EURUSD=X"], axis=0)

        # Remplacer les valeurs dans df
        common_columns = df.columns.intersection(df_filtered.columns)
        df[common_columns] = df_filtered[common_columns]

        return df
    
    def download_tickers_sma(self, start_date: datetime, end_date: datetime, tickers: list, sma: list) -> pd.DataFrame:
        """
        Calcule la moyenne mobile simple (SMA) pour chaque ticker dans le DataFrame des prix des tickers
        sur une période donnée.

        Args:
            start_date (datetime): La date de début pour le calcul de la SMA.
            end_date (datetime): La date de fin pour le calcul de la SMA.
            tickers (list): Liste des symboles boursiers à télécharger.
            sma (list): Liste des périodes (en jours) pour lesquelles calculer la SMA.

        Returns:
            pd.DataFrame: DataFrame contenant les SMA calculées pour chaque période et chaque ticker.
        """
        assert isinstance(start_date, datetime), "start_date doit être un objet datetime"
        assert isinstance(end_date, datetime), "end_date doit être un objet datetime"
        assert isinstance(tickers, list) and all(isinstance(ticker, str) for ticker in tickers), "tickers doit être une liste de chaînes de caractères"
        assert isinstance(sma, list) and all(isinstance(sma_day, int) for sma_day in sma), "sma doit être une liste d'entiers"

        ticker_prices = self.download_tickers_price(tickers, (start_date - timedelta(max(sma) + 50)), end_date)
        sma_df = pd.DataFrame()  # Initialiser avec les mêmes index que ticker_price_df

        for num_days in sma:
            # Calculer la moyenne mobile pour chaque ticker (chaque colonne de ticker_price_df)
            moving_average = ticker_prices.rolling(window=num_days).mean()
            
            # Ajouter chaque colonne SMA avec un suffixe du nombre de jours
            for col in moving_average.columns:
                sma_df[f"{col}_SMA_{num_days}"] = moving_average[col]

        return sma_df

    @staticmethod
    def calculate_dividend_evolution(portfolio_gross_price_evolution: pd.DataFrame, ticker_price_df: pd.DataFrame) -> pd.DataFrame:
        """
        Calcule l'évolution des dividendes pour chaque ticker d'un portefeuille, basée sur les prix bruts et les dividendes distribués.

        Args:
            portfolio_gross_price_evolution (pd.DataFrame): DataFrame contenant l'évolution brute des prix des tickers du portefeuille.
            ticker_price_df (pd.DataFrame): DataFrame contenant les prix des tickers correspondants.

        Returns:
            pd.DataFrame: DataFrame contenant l'évolution des dividendes pour chaque ticker, répartis sur les dates du portefeuille.
        """
        assert isinstance(portfolio_gross_price_evolution, pd.DataFrame), "portfolio_gross_price_evolution doit être un DataFrame"
        assert isinstance(ticker_price_df, pd.DataFrame), "ticker_price_df doit être un DataFrame"

        # Vérification des types de données dans les DataFrames
        assert all(isinstance(date, pd.Timestamp) for date in portfolio_gross_price_evolution.index), "Les index de portfolio_gross_price_evolution doivent être de type pd.Timestamp"

        # Initialiser le DataFrame des dividendes avec des zéros
        tickers_dividends = pd.DataFrame(0, index=portfolio_gross_price_evolution.index, columns=portfolio_gross_price_evolution.columns, dtype=float)

        for ticker in portfolio_gross_price_evolution.columns:
            # Téléchargement des données de dividendes
            stock = yf.Ticker(ticker)
            dividends = stock.dividends

            # S'assurer que l'index des dividendes est timezone-naive pour comparaison
            if dividends.index.tz is not None:
                dividends.index = dividends.index.tz_localize(None)

            # Filtrage des dividendes dans la plage de dates spécifiée
            dividends = dividends.loc[ticker_price_df.index.min():ticker_price_df.index.max()]

            # Ajout des dividendes au DataFrame, avec propagation aux dates suivantes
            for date, dividend_amount in dividends.items():
                if date in tickers_dividends.index:
                    # Calculer et ajouter le montant du dividende
                    dividend_amount_added = (dividend_amount * portfolio_gross_price_evolution.at[date, ticker] / ticker_price_df.at[date, ticker])
                    tickers_dividends.at[date, ticker] += dividend_amount_added

        return tickers_dividends


    def initialise_transaction_portfolio(self, transactions: list):
        transaction_portfolio = pd.DataFrame(columns=['ticker', 'operation', 'stock_price', 'amount', 'quantity', 'fees'])

        for data in transactions:
            transaction_portfolio.loc[data["date"], 'ticker'] = data['ticker']
            transaction_portfolio.loc[data["date"], 'operation'] = data['operation']
            transaction_portfolio.loc[data["date"], 'stock_price'] = self.tickers_prices.at[data["date"], data['ticker']]
            transaction_portfolio.loc[data["date"], 'amount'] = data['amount']
            transaction_portfolio.loc[data["date"], 'quantity'] = data['amount'] / self.tickers_prices.at[data["date"], data['ticker']]
            transaction_portfolio.loc[data["date"], 'fees'] = 0

        return transaction_portfolio

    def weighted_average_purchase_price(self, transaction_df: pd.DataFrame) -> pd.DataFrame:
        """
        Calcule le prix moyen pondéré d'achat pour chaque ticker dans le portefeuille.
        Cette méthode télécharge les prix de clôture pour chaque ticker, puis calcule le montant investi cumulé
        pour chaque date d'achat.

        Returns:
            tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
                - tickers_invested_amounts : DataFrame des montants investis pour chaque ticker à chaque date d'achat.
                - cumulative_invested_amounts : DataFrame des montants investis cumulés pour chaque ticker.
        """
        
        # On récupère tous les tickers achetés
        tickers_buy = transaction_df["ticker"].unique()

        tickers_invested_amounts = pd.DataFrame(0.0, index=self.tickers_prices.index, columns=self.tickers_prices.columns, dtype=float)

        # Pour chaque ticker acheté
        for ticker in tickers_buy:
            ticker_purchase_dates = transaction_df[transaction_df["ticker"] == ticker]
            quantity_ticker = 0

            # On boucle sur chaque transaction pour ce ticker
            for date, data in ticker_purchase_dates.iterrows():
                # Si c'est une opération d'achat
                if data["operation"] == "buy":
                    tickers_invested_amounts.loc[date, ticker] += (data["amount"])
                    quantity_ticker += data["quantity"]

        return tickers_invested_amounts

    def investment_amount_evolution(self, transaction_df: pd.DataFrame) -> pd.Series:
        """
        Calcule l'évolution du montant total investi dans le portefeuille au fil du temps.

        Cette fonction suit les investissements en ajoutant les montants investis aux dates d'achat 
        et en mettant à zéro les montants aux dates de vente.

        Returns:
            pd.Series: Série contenant l'évolution quotidienne du montant investi, avec les dates en index.
        """
        
        # On récupère tous les tickers achetés
        tickers_buy = transaction_df["ticker"].unique()
        # On initialise un dictionnaire pour les investissements
        date_range = pd.date_range(self.start_date, self.end_date)
        invested_amounts = pd.DataFrame(0.0, index=date_range, columns=tickers_buy)

        # Pour chaque ticker acheté
        for ticker in tickers_buy:
            ticker_purchase_dates = transaction_df[transaction_df["ticker"] == ticker]
            quantity_ticker = 0

            # On boucle sur chaque transaction pour ce ticker
            for date, data in ticker_purchase_dates.iterrows():
                # Si c'est une opération d'achat
                if data["operation"] == "buy":
                    invested_amounts.loc[date:, ticker] += (data["amount"])
                    quantity_ticker += data["quantity"]
                elif data["operation"] == "sell":
                    # Vente partielle ou totale, selon la quantité vendue
                    sell_quantity = data["quantity"]
                    sell_amount = (data["amount"])

                    if round(quantity_ticker, 6) > round(sell_quantity, 6):
                        # Vente partielle : on ajuste la quantité restante et l'investissement
                        invested_amounts.loc[date:, ticker] -= (sell_amount * (sell_quantity / quantity_ticker))
                    else:
                        # Vente totale : on réinitialise l'investissement à 0
                        invested_amounts.loc[date:, ticker] = 0.0

        return invested_amounts

    def initial_invested_amount(self) -> float:
        """
        Calcule l'argent investi initialement.

        Il faut calculer la somme des montants investis pour chaque ticker à chaque date d'achat.
        Puis on soustrait l'argent initialement investi du ticker s'il a été vendu.

        Returns:
            float: La différence entre la somme des dépôts (net de frais) et le cash disponible après achats/ventes.
        """
        # S'assurer que les colonnes sont bien en float
        self.transactions[['amount', 'fees']] = self.transactions[['amount', 'fees']].astype(float)

        # Calcule des dépôts nets
        deposits = self.transactions[self.transactions['operation'] == 'deposit']
        total_deposits = (deposits['amount'] - deposits['fees']).sum()

        # Calcule du cash disponible après achats/ventes
        cash_amount = total_deposits

        for _, row in self.transactions.iterrows():
            if row['operation'] == 'buy':
                cash_amount -= row['amount']
            elif row['operation'] == 'sell':
                cash_amount += row['amount']

        # Montant initialement investi = total des dépôts - cash disponible
        return total_deposits - cash_amount
