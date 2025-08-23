import pandas as pd
from api.services.modules.portfolios.base_portfolio import BasePortfolio

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

        investment_dates = self.get_dca_dcv_investment_dates()

        for portfolio in self.portfolio_allocation:
            portfolio_name = portfolio[-1]
            tickers = list(portfolio[0].keys())
            filtered_tickers_prices = self.tickers_prices.loc[:, self.tickers_prices.columns.intersection(tickers)]
            investment_amounts = {date: (self.money / len(investment_dates)) for date in investment_dates}
            portfolio_transactions = self.initialise_transactions_portfolio(self.create_transaction_dca(investment_amounts, portfolio[0]))

            # Tickers
            ticker_invested_amounts = self.tickers_investment_amount_evolution(portfolio_transactions)
            tickers_pru = self.calculate_pru(portfolio_transactions, ticker_invested_amounts)
            tickers_valuation, tickers_gain_pct, tickers_gain = self.capital_gain_losses_composed(ticker_invested_amounts, tickers_pru, filtered_tickers_prices)

            # Portefeuille
            portfolio_valuation = tickers_valuation.sum(axis=1)
            portfolio_realized_gains_losses = self.compute_plus_value_evolution(portfolio_transactions, ticker_invested_amounts)["plus_value_cumulative"]
            portfolio_gain = tickers_gain.sum(axis=1) + portfolio_realized_gains_losses
            # L'argent investi correspond à l'argent investi dans les tickers en enlevant les plus et moins values réalisées
            invested_money = (ticker_invested_amounts.sum(axis=1).iloc[-1] - portfolio_realized_gains_losses.iloc[-1])
            portfolio_gain_pct = self.calculate_portfolio_percentage_change(portfolio_gain, invested_money)

            
            self.tickers_twr[portfolio_name] = tickers_gain_pct
            self.tickers_gain[portfolio_name] = tickers_gain
            self.tickers_valuation[portfolio_name] = tickers_valuation
            self.tickers_dividends[portfolio_name] = self.calculate_dividends_evolution(tickers_valuation, filtered_tickers_prices)
            self.ticker_invested_amounts[portfolio_name] = ticker_invested_amounts
            self.tickers_pru[portfolio_name] = tickers_pru

            self.portfolio_twr[portfolio_name] = portfolio_gain_pct
            self.portfolio_gain[portfolio_name] = portfolio_gain
            self.portfolio_valuation[portfolio_name] = portfolio_valuation
            self.portfolio_invested_amounts[portfolio_name] = ticker_invested_amounts.sum(axis=1)
            self.portfolio_monthly_percentages[portfolio_name] = self.calculate_monthly_percentage_change(
                portfolio_valuation,
                portfolio_transactions
            )
            self.portfolio_cagr[portfolio_name] = self.calculate_portfolio_cagr(portfolio_valuation)
            self.portfolio_cash[portfolio_name] = self.compute_cash_evolution(portfolio_transactions)["cash_cumulative"]
            self.portfolio_fees[portfolio_name] = self.compute_fees_evolution(portfolio_transactions)["cumulative_fees"]
            self.portfolio_dividend_yield[portfolio_name] = self.calculate_dividend_yield(portfolio_transactions, portfolio_valuation)
            self.portfolio_dividend_earn[portfolio_name] = self.calculate_dividend_earn(portfolio_transactions)

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

            # graphique(tickers_gain_pct, "TWR")
            # graphique(tickers_gain, "Gains €")
            # graphique(tickers_valuation, "Valorisation")
            # graphique(ticker_invested_amounts, "Argent investis cumulées")
            # graphique(self.calculate_dividends_evolution(tickers_valuation, tickers_prices), "Dividendes par tickers")
            # graphique(tickers_pru, "PRU tickers")

            # graphique(portfolio_valuation, "portfolio_valuation")
            # graphique(portfolio_gain, "Portefeuille €")
            # graphique(portfolio_gain_pct, "Portefeuille %")


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

    def initialise_transactions_portfolio(self, transactions: list) -> pd.DataFrame:
        rows = []
        for t in transactions:
            price = self.tickers_prices.at[t["date"], t["ticker"]]
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
    