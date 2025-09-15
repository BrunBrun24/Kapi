from datetime import datetime
from .base_portfolio import BasePortfolio

import pandas as pd

class MyPortfolio():

    def my_portfolio(self, transactions: pd.DataFrame, tickers_prices: pd.DataFrame, start_date: datetime, end_date: datetime):
        base_portfolio = BasePortfolio(start_date, end_date)

        tickers_invested_amounts = base_portfolio.tickers_investment_amount_evolution(transactions)
        tickers_pru = base_portfolio.calculate_pru(transactions, tickers_invested_amounts)
        tickers_valuation, tickers_twr, tickers_gain = base_portfolio.capital_gain_losses_composed(tickers_invested_amounts, tickers_pru, tickers_prices)
        tickers_dividends = self.calculate_dividends(transactions, start_date, end_date)

        return {
            "tickers_invested_amounts": tickers_invested_amounts,
            "tickers_twr": tickers_twr,
            "tickers_gain": tickers_gain,
            "tickers_valuation": tickers_valuation,
            "tickers_dividends": tickers_dividends,
            "tickers_pru": tickers_pru,
        }

    def calculate_dividends(self, transactions: pd.DataFrame, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """
        Calcule les dividendes nets (dividende - frais) reçus pour chaque ticker,
        sur toute la période du portefeuille, et les organise par date.

        Cette méthode :
        - filtre les opérations de type `'dividend'` dans le portefeuille ;
        - agrège les montants nets (après frais) par date et par ticker ;
        - retourne un DataFrame quotidien contenant les dividendes reçus.

        Returns
        -------
        pd.DataFrame
            DataFrame indexé par date (`DatetimeIndex`) avec :
            - colonnes = tickers pour lesquels des dividendes ont été versés ;
            - valeurs = montant net du dividende reçu ce jour-là (0.0 si aucun).
        """

        # Filtre les transactions de type 'dividend'
        dividends_df = transactions[transactions["operation"] == "dividend"].copy()

        # S'assure que la colonne 'date' est bien en datetime (au cas où)
        dividends_df.index = pd.to_datetime(dividends_df.index)

        # Nettoie les tickers
        tickers = dividends_df["ticker"].dropna().unique()

        # Crée une plage de dates complète
        date_range = pd.date_range(start=start_date, end=end_date)

        # Initialise le DataFrame des dividendes
        cash_amount = pd.DataFrame(0.0, index=date_range, columns=tickers)

        # Agrège les montants par date et ticker
        for date, row in dividends_df.iterrows():
            ticker = row["ticker"]
            amount = float(row["amount"]) - float(row.get("fees", 0.0))  # Sécurité sur les frais
            if pd.notna(ticker) and date in cash_amount.index:
                cash_amount.at[date, ticker] += amount

        return cash_amount
