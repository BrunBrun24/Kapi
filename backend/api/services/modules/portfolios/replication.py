from api.services.modules.portfolios.base_portfolio import BasePortfolio

import pandas as pd

class Replication(BasePortfolio):
        
    def replication_my_portfolio(self):
        """Cette méthode permet de simuler en fonction de différents portefeuilles, un investissement d'après les mêmes dates d'achats et de ventes dans mon portefeuille initiale"""

        for portfolio in self.portfolio_allocation:
            portfolio_name = portfolio[-1] + " Réplication"
            tickers = list(portfolio[0].keys())
            tickers_prices = self.tickers_prices.loc[:, self.tickers_prices.columns.intersection(tickers)]
            portfolio_transactions = self.created_transactions(portfolio)

            # Tickers
            ticker_invested_amounts = self.tickers_investment_amount_evolution(portfolio_transactions)
            tickers_pru = self.calculate_pru(portfolio_transactions, ticker_invested_amounts)
            tickers_valuation, tickers_gain_pct, tickers_gain = self.capital_gain_losses_composed(ticker_invested_amounts, tickers_pru, tickers_prices)

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
            self.tickers_dividends[portfolio_name] = self.calculate_dividends_evolution(tickers_valuation, tickers_prices)
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

            self.cash[portfolio_name] = self.compute_cash_evolution(portfolio_transactions)["cash_cumulative"]
            self.fees[portfolio_name] = self.compute_fees_evolution(portfolio_transactions)["cumulative_fees"]

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

    def created_transactions(self, portfolio: dict) -> pd.DataFrame:
        transactions_buy_sell = self.transactions[self.transactions["operation"].isin(["buy", "sell", "interest"])]

        rows = []
        for date, row in transactions_buy_sell.iterrows():
            if (row["operation"] == "buy") or (row["operation"] == "sell"):
                for ticker, pct in portfolio[0].items():
                    price = self.tickers_prices.at[date, ticker]
                    if (row["operation"] == "buy"):
                        amount = ((row["amount"] - row["fees"]) * pct / 100)
                    else:
                        amount = ((row["amount"]) / len(portfolio[0].keys()))

                    rows.append(
                        {
                            "date": date,
                            "ticker": ticker,
                            "operation": row["operation"],
                            "stock_price": price,
                            "amount": amount,
                            "quantity": amount / price,
                            "fees": 0.0,
                        }
                    )
            elif (row["operation"] == "interest"):
                rows.append(
                    {
                        "date": date,
                        "ticker": None,
                        "operation": row["operation"],
                        "stock_price": None,
                        "amount": row["amount"],
                        "quantity": None,
                        "fees": 0.0,
                    }
                )

        transaction_portfolio = pd.DataFrame(rows).set_index("date")
        transaction_portfolio.sort_index(inplace=True)

        return transaction_portfolio
