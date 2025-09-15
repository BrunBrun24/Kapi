from datetime import datetime
import pandas as pd
from api.services.modules.portfolios.base_portfolio import BasePortfolio

class DollarCostAveraging():

    def dca(self, portfolio: dict, tickers_prices: pd.DataFrame, money: float, start_date: datetime, end_date: datetime):
        """
        Cette méthode permet de simuler un investissement en Dollar Cost Average (DCA) en fonction de différents portefeuilles.

        Explication:
            L’investissement en DCA (Dollar-Cost Averaging) est une stratégie simple mais efficace,
            qui consiste à investir régulièrement des montants fixes dans un actif financier, indépendamment de son prix.
            Plutôt que d'essayer de deviner le meilleur moment pour investir, le DCA permet d'acheter des parts de façon continue,
            réduisant l'impact des fluctuations du marché.
        """

        base_portfolio = BasePortfolio(start_date, end_date)

        investment_dates = self.get_dca_dcv_investment_dates(start_date, end_date)

        # Gérer les dates manquantes dans ticker_prices
        # 1. Normaliser les dates
        tickers_prices.index = pd.to_datetime(tickers_prices.index).normalize()
        # 2. Créer toutes les dates
        all_dates = pd.date_range(start=start_date, end=end_date, freq='D')
        # 3. Reindex et propager les valeurs
        tickers_prices = tickers_prices.reindex(all_dates).ffill().bfill()

        tickers = list(portfolio[0].keys())
        filtered_tickers_prices = tickers_prices.loc[:, tickers_prices.columns.intersection(tickers)]
        investment_amounts = {date: (money / len(investment_dates)) for date in investment_dates}
        portfolio_transactions = self.initialise_transactions_portfolio(self.create_transaction_dca(investment_amounts, portfolio[0]), tickers_prices)

        # Tickers
        tickers_invested_amounts = base_portfolio.tickers_investment_amount_evolution(portfolio_transactions)
        tickers_pru = base_portfolio.calculate_pru(portfolio_transactions, tickers_invested_amounts)
        tickers_valuation, tickers_gain_pct, tickers_gain = base_portfolio.capital_gain_losses_composed(tickers_invested_amounts, tickers_pru, filtered_tickers_prices)

        # Portefeuille
        portfolio_valuation = tickers_valuation.sum(axis=1)
        portfolio_realized_gains_losses = base_portfolio.compute_plus_value_evolution(portfolio_transactions, tickers_invested_amounts)["plus_value_cumulative"]
        portfolio_gain = tickers_gain.sum(axis=1) + portfolio_realized_gains_losses
        # L'argent investi correspond à l'argent investi dans les tickers en enlevant les plus et moins values réalisées
        invested_money = (tickers_invested_amounts.sum(axis=1).iloc[-1] - portfolio_realized_gains_losses.iloc[-1])
        portfolio_gain_pct = base_portfolio.calculate_portfolio_percentage_change(portfolio_gain, invested_money)
        
        tickers_twr = tickers_gain_pct
        tickers_gain = tickers_gain
        tickers_valuation = tickers_valuation
        tickers_dividends = base_portfolio.calculate_dividends_evolution(tickers_valuation, filtered_tickers_prices)
        tickers_invested_amounts = tickers_invested_amounts
        tickers_pru = tickers_pru

        portfolio_twr = portfolio_gain_pct
        portfolio_gain = portfolio_gain
        portfolio_valuation = portfolio_valuation
        portfolio_invested_amounts = tickers_invested_amounts.sum(axis=1)
        portfolio_monthly_percentages = base_portfolio.calculate_monthly_percentage_change(
            portfolio_valuation,
            portfolio_transactions
        )
        portfolio_cagr = base_portfolio.calculate_portfolio_cagr(portfolio_valuation, portfolio_invested_amounts)
        portfolio_cash = base_portfolio.compute_cash_evolution(portfolio_transactions)["cash_cumulative"]
        portfolio_fees = base_portfolio.compute_fees_evolution(portfolio_transactions)["cumulative_fees"]
        portfolio_dividend_yield = base_portfolio.calculate_dividend_yield(portfolio_transactions, portfolio_valuation)
        portfolio_dividend_earn = base_portfolio.calculate_dividend_earn(portfolio_transactions)
        
        return {
            "tickers_invested_amounts": tickers_invested_amounts,
            "tickers_twr": tickers_twr,
            "tickers_gain": tickers_gain,
            "tickers_valuation": tickers_valuation,
            "tickers_dividends": tickers_dividends,
            "tickers_pru": tickers_pru,
            
            "portfolio_twr": portfolio_twr,
            "portfolio_gain": portfolio_gain,
            "portfolio_valuation": portfolio_valuation,
            "portfolio_invested_amounts": portfolio_invested_amounts,
            "portfolio_monthly_percentages": portfolio_monthly_percentages,
            "portfolio_cagr": portfolio_cagr,
            "portfolio_cash": portfolio_cash,
            "portfolio_fees": portfolio_fees,
            "portfolio_dividend_yield": portfolio_dividend_yield,
            "portfolio_dividend_earn": portfolio_dividend_earn,
        }

    @staticmethod
    def get_dca_dcv_investment_dates(start_date: datetime, end_date: datetime) -> list:
        """
        Extrait les dates de début de chaque mois dans la plage donnée entre start_date et end_date.

        Returns:
            list: Liste des dates de début de chaque mois sous forme de chaînes formatées 'YYYY-MM-DD'.
        """

        # Initialisation de la liste pour stocker les dates de début de chaque mois
        start_of_months = []
        current_date = start_date

        while current_date <= end_date:
            # Ajouter la date de début du mois formatée
            start_of_months.append(current_date)

            # Passer au mois suivant
            next_month = current_date.month % 12 + 1
            next_year = current_date.year + (current_date.month // 12)
            current_date = current_date.replace(month=next_month, year=next_year, day=1)

        return sorted(start_of_months)

    @staticmethod
    def create_transaction_dca(buy_transactions: dict, portfolio: dict) -> list[dict]:
        result = []

        for date, amount in buy_transactions.items():
            for ticker, percentage in portfolio.items():
                transaction = {}
                transaction["date"] = date
                transaction["ticker"] = ticker
                transaction["operation"] = "buy"
                transaction["amount"] = (amount * percentage / 100)

                result.append(transaction)

        return result

    @staticmethod
    def initialise_transactions_portfolio(transactions: list, tickers_prices: pd.DataFrame) -> pd.DataFrame:
        rows = []
        for t in transactions:
            price = tickers_prices.at[t["date"], t["ticker"]]
            rows.append(
                {
                    "date": t["date"],
                    "ticker": t["ticker"],
                    "operation": t["operation"],
                    "stock_price": price,
                    "amount": t["amount"],
                    "quantity": t["amount"] / price,
                    "fees": 0.0,
                }
            )

        transaction_portfolio = pd.DataFrame(rows).set_index("date")
        transaction_portfolio.sort_index(inplace=True)

        return transaction_portfolio
    