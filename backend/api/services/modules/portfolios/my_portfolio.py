from .base_portfolio import BasePortfolio

import pandas as pd
from datetime import timedelta
import numpy as np

class MyPortfolio(BasePortfolio):

    def my_portfolio(self, name_portfolio: str):
        """Cette méthode permet de simuler en fonction de différents portefeuilles, un investissement d'après les mêmes dates d'achats et de ventes dans mon portefeuille initiale"""

        cash = self.calculate_cash(self.transactions)
        print(cash)
        print(self.initial_invested_amount())
        cumulative_invested_amounts = self.investment_amount_evolution(self.transactions)
        self.total_invested_amounts[name_portfolio] = cumulative_invested_amounts.sum(axis=1)
        self.tickers_prices = self.download_tickers_price([ticker for ticker in self.transactions["ticker"].dropna().unique() if pd.notna(ticker)], self.start_date, self.end_date)

        invested_amounts_tickers = self.weighted_average_purchase_price(self.transactions)

        # Calcul des montants
        money_evolution_tickers, sales_evolution_tickers, gains_losses_evolution_tickers = self.capital_gain_losses_composed(invested_amounts_tickers, self.tickers_prices)

        money_evolution_portfolio = money_evolution_tickers.sum(axis=1)
        gains_losses_evolution_portfolio = gains_losses_evolution_tickers.sum(axis=1) + self.capital_gains_realized_net(cumulative_invested_amounts)
        
        # Calcul des pourcentages
        ticker_percentage_evolution = self.calculate_percentage_evolution_tickers(money_evolution_tickers, cumulative_invested_amounts)
        portfolio_percentage_evolution = self.calculate_portfolio_percentage_change(gains_losses_evolution_portfolio, self.initial_invested_amount())
        
        self.portfolio_twr[name_portfolio] = portfolio_percentage_evolution
        self.portfolio_net_price[name_portfolio] = gains_losses_evolution_portfolio
        self.ticker_twr[name_portfolio] = ticker_percentage_evolution
        self.tickers_net_prices[name_portfolio] = gains_losses_evolution_tickers
        self.tickers_gross_prices[name_portfolio] = money_evolution_tickers
        self.portfolio_monthly_percentages[name_portfolio] = self.calculate_monthly_percentage_change(
            money_evolution_tickers.sum(axis=1),
            self.transactions
        )
        self.tickers_dividends[name_portfolio] = self.calculate_dividends()
        self.tickers_funds_invested[name_portfolio] = cumulative_invested_amounts
        self.tickers_invested_amounts[name_portfolio] = invested_amounts_tickers
        self.tickers_sold_amounts[name_portfolio] = sales_evolution_tickers
        self.bank_balance[name_portfolio] = (cash + money_evolution_portfolio)
        self.cash[name_portfolio] = cash

    def capital_gain_losses_composed(self, tickers_invested_amounts: pd.DataFrame, tickers_prices: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        assert isinstance(tickers_invested_amounts, pd.DataFrame), "tickers_invested_amounts doit être un DataFrame"
        assert isinstance(tickers_prices, pd.DataFrame), "tickers_prices doit être un DataFrame"
        
        money_evolution_tickers = pd.DataFrame(index=tickers_prices.index, columns=tickers_prices.columns, dtype=float)
        sales_evolution_tickers = pd.DataFrame(index=tickers_prices.index, columns=tickers_prices.columns, dtype=float)
        gains_losses_evolution_tickers = pd.DataFrame(index=tickers_prices.index, columns=tickers_prices.columns, dtype=float)

        tickers = list(tickers_prices.columns)

        # Calcul de la plus-value composée pour chaque jour
        for ticker in tickers:
            sales_dates_prices = self.transactions[self.transactions["ticker"] == ticker]
            sales_dates_prices = sales_dates_prices[sales_dates_prices["operation"] == "sell"]
            
            # Initialiser avec la valeur d'achat initiale pour chaque ticker
            money_evolution_tickers.loc[tickers_prices.index[0], ticker] = tickers_invested_amounts.loc[tickers_prices.index[0], ticker]
            gains_losses_evolution_tickers.loc[tickers_prices.index[0], ticker] = 0

            invested_amount_cumulative = tickers_invested_amounts.loc[tickers_prices.index[0], ticker]

            for i in range(1, len(tickers_prices.index)):
                previous_date = tickers_prices.index[i-1]
                current_date = tickers_prices.index[i]

                # Calcul de l'évolution en pourcentage entre le jour actuel et le jour précédent
                percentage_evolution = (tickers_prices.loc[current_date, ticker] / tickers_prices.loc[previous_date, ticker]) - 1
                
                # Calcule l'évolution globale du portefeuille
                money_evolution_tickers.loc[current_date, ticker] = money_evolution_tickers.loc[previous_date, ticker] * (1 + percentage_evolution)
                # Calcule l'évolution des gains et pertes
                gains_losses_evolution_tickers.loc[current_date, ticker] = (money_evolution_tickers.loc[current_date, ticker] - invested_amount_cumulative)
                
                if tickers_invested_amounts.loc[previous_date, ticker] != tickers_invested_amounts.loc[current_date, ticker]:
                    money_evolution_tickers.loc[current_date, ticker] += tickers_invested_amounts.loc[current_date, ticker]
                    invested_amount_cumulative += tickers_invested_amounts.loc[current_date, ticker]

                if current_date in sales_dates_prices.index:
                    money_removed_for_ticker = sales_dates_prices.loc[current_date, "amount"]
                    money_evolution_tickers.loc[current_date, ticker] -= money_removed_for_ticker
                    sales_evolution_tickers.loc[current_date, ticker] = money_removed_for_ticker

                    if ((money_evolution_tickers.loc[current_date, ticker] - money_removed_for_ticker) <= 0):
                        money_evolution_tickers.loc[current_date, ticker] = 0
                        invested_amount_cumulative = 0

        money_evolution_tickers = money_evolution_tickers.replace(0, np.nan)
        gains_losses_evolution_tickers = gains_losses_evolution_tickers.replace(0, np.nan)

        return money_evolution_tickers, sales_evolution_tickers, gains_losses_evolution_tickers
    
    def capital_gains_realized_net(self, cumulative_invested_amounts: pd.DataFrame) -> pd.Series:
        """
        Calcule les plus-values net réalisées sur une période donnée en tenant compte des opérations d'achat et de vente d'investissements.

        Returns:
            pd.DataFrame: Un DataFrame indexé par une plage de dates, contenant les plus-values cumulées réalisées sur la période.
        """

        date_range = pd.date_range(start=self.start_date, end=self.end_date)
        net_realized_gains = pd.Series(0.0, index=date_range)

        sales_dates = self.transactions[self.transactions["operation"] == "sell"]

        for sale_date, data in sales_dates.iterrows():
            # Calculer la plus-value nette réalisée
            net_realized_gains.loc[sale_date:] += (data["amount"] + data["fees"]) - cumulative_invested_amounts.loc[(sale_date - timedelta(days=1)), data["ticker"]]

        return net_realized_gains

    def calculate_cash(self, transactions_df) -> float:
        # Initialise le cash
        cash = 0.0

        # Opérations entrantes (ajout d'argent)
        deposit = transactions_df.loc[transactions_df['operation'] == 'deposit', 'amount'].sum()
        deposit_fees = transactions_df.loc[transactions_df['operation'] == 'deposit', 'fees'].sum()

        interest = transactions_df.loc[transactions_df['operation'] == 'interest', 'amount'].sum()
        interest_fees = transactions_df.loc[transactions_df['operation'] == 'interest', 'fees'].sum()

        dividend = transactions_df.loc[transactions_df['operation'] == 'dividend', 'amount'].sum()
        dividend_fees = transactions_df.loc[transactions_df['operation'] == 'dividend', 'fees'].sum()

        sell = transactions_df.loc[transactions_df['operation'] == 'sell', 'amount'].sum()
        sell_fees = transactions_df.loc[transactions_df['operation'] == 'sell', 'fees'].sum()

        # Opérations sortantes (sortie d'argent)
        buy = transactions_df.loc[transactions_df['operation'] == 'buy', 'amount'].sum()
        buy_fees = transactions_df.loc[transactions_df['operation'] == 'buy', 'fees'].sum()

        withdrawal = transactions_df.loc[transactions_df['operation'] == 'withdrawal', 'amount'].sum()
        withdrawal_fees = transactions_df.loc[transactions_df['operation'] == 'withdrawal', 'fees'].sum()

        # Calcul du cash
        cash = (
            (deposit - deposit_fees)
            + (interest - interest_fees)
            + (dividend - dividend_fees)
            + (sell - sell_fees)
            - (buy + buy_fees)
            - (withdrawal + withdrawal_fees)
        )

        return float(cash)
    
    def calculate_dividends(self) -> pd.DataFrame:
        """Calcule les dividendes reçus par date et par ticker."""

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
