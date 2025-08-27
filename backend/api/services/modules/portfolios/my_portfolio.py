from datetime import datetime
from .base_portfolio import BasePortfolio

import pandas as pd

class MyPortfolio(BasePortfolio):
    def __init__(self, transactions_df: pd.DataFrame, tickers_prices: pd.DataFrame, start_date: datetime = None, tickers_valuations: dict = {}):
        self.transactions = transactions_df

        self.start_date = transactions_df.index[0]
        self.end_date = pd.to_datetime(tickers_prices.index[-1])

        self.tickers_prices = tickers_prices

        # Gérer les dates manquantes dans ticker_prices
        # 1. Normaliser les dates
        self.tickers_prices.index = pd.to_datetime(self.tickers_prices.index).normalize()
        # 2. Créer toutes les dates
        all_dates = pd.date_range(start=self.start_date, end=self.end_date, freq='D')
        # 3. Reindex et propager les valeurs
        self.tickers_prices = self.tickers_prices.reindex(all_dates).ffill().bfill()

        if start_date is not None:
            self.transactions = self.set_transaction_with_date(transactions_df, start_date, tickers_valuations, self.tickers_prices)
            self.start_date = self.transactions.index[0]

        # portfolio_percentage = [
        #     [{'SPY': 100}, 'S&P 500'],
        #     [{'NQ=F': 100}, 'Nasdaq 100'],
        #     [{'URTH': 100}, 'MSCI WORLD'],
        #     [{'^FCHI': 100}, 'CAC 40'],
        # ]
        # self.set_portfolio_allocation(portfolio_percentage)
        # self.dca()

        # if start_date is None:
        #     self.save_portfolio_performance()


        # Tickers
        tickers_invested_amounts = self.tickers_investment_amount_evolution(self.transactions)
        tickers_pru = self.calculate_pru(self.transactions, tickers_invested_amounts)
        tickers_valuation, tickers_gain_pct, tickers_gain = self.capital_gain_losses_composed(tickers_invested_amounts, tickers_pru, self.tickers_prices)

        self.tickers_twr = tickers_gain_pct
        self.tickers_gain = tickers_gain
        self.tickers_valuation = tickers_valuation
        self.tickers_dividends = self.calculate_dividends()
        self.tickers_invested_amounts = tickers_invested_amounts
        self.tickers_pru = tickers_pru


        def graphique(df, title):
            import plotly.express as px
            # Transformer le DataFrame en format long (melt)
            df_melt = df.reset_index().melt(id_vars='index', var_name='Action', value_name='Prix')

            # Tracer
            fig = px.line(df_melt, x='index', y='Prix', color='Action', title=title)
            fig.update_layout(
                xaxis_title='Date',
                yaxis_title='Prix (€)',
                height=920,
                template='plotly_white'
            )
            fig.show()

        # graphique(tickers_invested_amounts, "Argent investis cumulées")
        # graphique(tickers_gain, "Gains €")
        # graphique(tickers_gain_pct, "TWR")
        # graphique(tickers_valuation, "Valorisation")
        # graphique(tickers_pru, "PRU tickers")
        # graphique(self.calculate_dividends(), "Dividendes par tickers")
        # graphique(self.compute_cash_evolution(self.transactions)["cash_cumulative"], "Cash")

        # graphique(portfolio_valuation, " Valorisation du portefeuille")
        # graphique(portfolio_gain, "Portefeuille €")
        # graphique(portfolio_gain_pct, "Portefeuille %")
        
        # graphique(self.compute_cash_evolution(self.transactions), "cash") # A REVOIR ERREUR contenue en négatif (IMPOSSIBLE)


    def calculate_dividends(self) -> pd.DataFrame:
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
        dividends_df = self.transactions[self.transactions["operation"] == "dividend"].copy()

        # S'assure que la colonne 'date' est bien en datetime (au cas où)
        dividends_df.index = pd.to_datetime(dividends_df.index)

        # Nettoie les tickers
        tickers = dividends_df["ticker"].dropna().unique()

        # Crée une plage de dates complète
        date_range = pd.date_range(start=self.start_date, end=self.end_date)

        # Initialise le DataFrame des dividendes
        cash_amount = pd.DataFrame(0.0, index=date_range, columns=tickers)

        # Agrège les montants par date et ticker
        for date, row in dividends_df.iterrows():
            ticker = row["ticker"]
            amount = float(row["amount"]) - float(row.get("fees", 0.0))  # Sécurité sur les frais
            if pd.notna(ticker) and date in cash_amount.index:
                cash_amount.at[date, ticker] += amount

        return cash_amount

    def get_performances(self) -> dict:
        return {
            "tickers_invested_amounts": self.tickers_invested_amounts,
            "tickers_twr": self.tickers_twr,
            "tickers_gain": self.tickers_gain,
            "tickers_valuation": self.tickers_valuation,
            "tickers_dividends": self.tickers_dividends,
            "tickers_pru": self.tickers_pru,
        }
