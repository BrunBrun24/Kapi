from api.services.modules.portfolios.base_portfolio import BasePortfolio
import pandas as pd

class DollarCostAveraging(BasePortfolio):

    def dca(self):
        """
        Cette méthode permet de simuler un investissement en Dollar Cost Average (DCA) en fonction de différents portefeuilles.

        Explication:
            L’investissement en DCA (Dollar-Cost Averaging) est une stratégie simple mais efficace,
            qui consiste à investir régulièrement des montants fixes dans un actif financier, indépendamment de son prix.
            Plutôt que d'essayer de deviner le meilleur moment pour investir, le DCA permet d'acheter des parts de façon continue,
            réduisant l'impact des fluctuations du marché.
        """

        tickers_prices = self.tickers_prices.copy()
        investment_dates = self.get_dca_dcv_investment_dates()

        for portfolio in self.portfolio_allocation:
            portfolio_name = portfolio[-1] + " DCA"
            tickers = list(portfolio[0].keys())
            filtered_tickers_prices = tickers_prices.loc[:, tickers_prices.columns.intersection(tickers)]
            money = self.initial_invested_amount()
            investment_amounts = {date: (money / len(investment_dates)) for date in investment_dates}
            transaction_portfolio = self.initialise_transaction_portfolio(self.create_transaction_dca(investment_amounts, portfolio[0]))

            invested_amounts_tickers = self.weighted_average_purchase_price(transaction_portfolio)
            cumulative_invested_amounts = self.investment_amount_evolution(transaction_portfolio)

            # Calcul des montants
            money_evolution_tickers, sales_evolution_tickers, gains_losses_evolution_tickers = self.capital_gain_losses_composed(invested_amounts_tickers, filtered_tickers_prices)
            portfolio_invested_amounts_evolution = money_evolution_tickers.sum(axis=1)
            portfolio_gains_losses_evolution = gains_losses_evolution_tickers.sum(axis=1)

            # Calcul des pourcentages
            tickers_percentage_evolution = self.calculate_percentage_evolution_tickers(money_evolution_tickers, cumulative_invested_amounts)
            portfolio_percentage_evolution = self.calculate_portfolio_percentage_change(portfolio_gains_losses_evolution, cumulative_invested_amounts.iloc[-1].sum())

            # On stock les DataFrames
            self.portfolio_twr[portfolio_name] = portfolio_percentage_evolution
            self.portfolio_net_price[portfolio_name] = portfolio_gains_losses_evolution
            self.ticker_twr[portfolio_name] = tickers_percentage_evolution
            self.tickers_net_prices[portfolio_name] = gains_losses_evolution_tickers
            self.tickers_gross_prices[portfolio_name] = money_evolution_tickers
            self.portfolio_monthly_percentages[portfolio_name] = self.calculate_monthly_percentage_change(
                portfolio_invested_amounts_evolution, 
                transaction_portfolio
            )
            self.tickers_funds_invested[portfolio_name] = cumulative_invested_amounts
            self.tickers_invested_amounts[portfolio_name] = invested_amounts_tickers
            self.tickers_sold_amounts[portfolio_name] = pd.DataFrame(index=filtered_tickers_prices.index, columns=filtered_tickers_prices.columns, dtype=float)
            self.bank_balance[portfolio_name] = portfolio_invested_amounts_evolution
            self.cash[portfolio_name] = portfolio_invested_amounts_evolution

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

    def get_dca_dcv_investment_dates(self) -> list:
        """
        Extrait les dates de début de chaque mois dans la plage donnée entre start_date et end_date.

        Returns:
            list: Liste des dates de début de chaque mois sous forme de chaînes formatées 'YYYY-MM-DD'.
        """

        start_date = self.start_date
        end_date = self.end_date

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
