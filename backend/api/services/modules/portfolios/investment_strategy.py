from datetime import datetime
import pandas as pd
from api.services.modules.portfolios.base_portfolio import BasePortfolio

class InvestmentStrategy:
    """
    Classe pour simuler des stratégies d'investissement sur un portefeuille donné.
    Supporte : stratégie générale, DCA (Dollar Cost Averaging) et réplication.
    """

    def run_strategy(
        self,
        portfolio: list,
        tickers_prices: pd.DataFrame,
        portfolio_transactions: pd.DataFrame,
        start_date: datetime,
        end_date: datetime
    ) -> dict:
        """
        Simule une stratégie d'investissement standard pour le portefeuille donné.
        """
        base_portfolio = BasePortfolio(start_date, end_date)

        tickers = list(portfolio[0].keys())
        filtered_prices = tickers_prices.loc[:, tickers_prices.columns.intersection(tickers)]

        # Calculs par ticker
        invested_amounts = base_portfolio.tickers_investment_amount_evolution(portfolio_transactions)
        pru = base_portfolio.calculate_pru(portfolio_transactions, invested_amounts)
        valuation, twr, gains = base_portfolio.capital_gain_losses_composed(invested_amounts, pru, filtered_prices)
        dividends = base_portfolio.calculate_dividends_evolution(valuation, filtered_prices)

        # Calculs portefeuille
        portfolio_valuation = valuation.sum(axis=1)
        realized_gains = base_portfolio.compute_plus_value_evolution(portfolio_transactions, invested_amounts)["plus_value_cumulative"]
        portfolio_gain = gains.sum(axis=1) + realized_gains
        invested_money = invested_amounts.sum(axis=1).iloc[-1] - realized_gains.iloc[-1]
        portfolio_twr = base_portfolio.calculate_portfolio_percentage_change(portfolio_gain, invested_money)
        portfolio_invested = invested_amounts.sum(axis=1)
        portfolio_monthly_pct = base_portfolio.calculate_monthly_percentage_change(portfolio_valuation, portfolio_transactions)
        portfolio_cagr = base_portfolio.calculate_portfolio_cagr(portfolio_valuation, portfolio_invested)
        portfolio_cash = base_portfolio.compute_cash_evolution(portfolio_transactions)["cash_cumulative"]
        portfolio_fees = base_portfolio.compute_fees_evolution(portfolio_transactions)["cumulative_fees"]
        portfolio_dividend_yield = base_portfolio.calculate_dividend_yield(portfolio_transactions, portfolio_valuation)
        portfolio_dividend_earn = base_portfolio.calculate_dividend_earn(portfolio_transactions)

        return {
            "tickers_invested_amounts": invested_amounts,
            "tickers_twr": twr,
            "tickers_gain": gains,
            "tickers_valuation": valuation,
            "tickers_dividends": dividends,
            "tickers_pru": pru,
            "portfolio_twr": portfolio_twr,
            "portfolio_gain": portfolio_gain,
            "portfolio_valuation": portfolio_valuation,
            "portfolio_invested_amounts": portfolio_invested,
            "portfolio_monthly_percentages": portfolio_monthly_pct,
            "portfolio_cagr": portfolio_cagr,
            "portfolio_cash": portfolio_cash,
            "portfolio_fees": portfolio_fees,
            "portfolio_dividend_yield": portfolio_dividend_yield,
            "portfolio_dividend_earn": portfolio_dividend_earn,
        }

    def simulate_dca(
        self,
        portfolio: list,
        tickers_prices: pd.DataFrame,
        money: float,
        start_date: datetime,
        end_date: datetime
    ) -> dict:
        """
        Simule un investissement en Dollar-Cost Averaging (DCA).
        """
        tickers_prices = self._fill_missing_dates(tickers_prices, start_date, end_date)
        investment_dates = self._get_monthly_investment_dates(start_date, end_date)
        investment_amounts = {date: money / len(investment_dates) for date in investment_dates}
        transactions = self._create_dca_transactions(investment_amounts, portfolio[0])
        portfolio_transactions = self._build_transaction_df(transactions, tickers_prices)

        return self.run_strategy(portfolio, tickers_prices, portfolio_transactions, start_date, end_date)

    def simulate_replication(
        self,
        portfolio: list,
        transactions: pd.DataFrame,
        tickers_prices: pd.DataFrame,
        start_date: datetime,
        end_date: datetime
    ) -> dict:
        """
        Simule un portefeuille selon les mêmes dates d'achats et ventes fournies.
        """
        tickers_prices = self._fill_missing_dates(tickers_prices, start_date, end_date)
        portfolio_transactions = self._replicate_transactions(portfolio, transactions, tickers_prices)

        return self.run_strategy(portfolio, tickers_prices, portfolio_transactions, start_date, end_date)

    # --------------------------
    # Méthodes utilitaires statiques
    # --------------------------
    @staticmethod
    def _fill_missing_dates(tickers_prices: pd.DataFrame, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Normalise les dates et remplit les valeurs manquantes par propagation."""
        tickers_prices.index = pd.to_datetime(tickers_prices.index).normalize()
        all_dates = pd.date_range(start=start_date, end=end_date, freq='D')
        return tickers_prices.reindex(all_dates).ffill().bfill()

    @staticmethod
    def _get_monthly_investment_dates(start_date: datetime, end_date: datetime) -> list:
        """Retourne la liste des dates de début de chaque mois."""
        dates = []
        current = start_date
        while current <= end_date:
            dates.append(current)
            next_month = current.month % 12 + 1
            next_year = current.year + (current.month // 12)
            current = current.replace(month=next_month, year=next_year, day=1)
        return sorted(dates)

    @staticmethod
    def _create_dca_transactions(amounts: dict, portfolio: dict) -> list:
        """Crée une liste de transactions DCA par ticker."""
        transactions = []
        for date, total in amounts.items():
            for ticker, pct in portfolio.items():
                transactions.append({
                    "date": date,
                    "ticker": ticker,
                    "operation": "buy",
                    "amount": total * pct / 100
                })
        return transactions

    @staticmethod
    def _build_transaction_df(transactions: list, tickers_prices: pd.DataFrame) -> pd.DataFrame:
        """Convertit une liste de transactions en DataFrame avec calcul des quantités."""
        data = {col: [] for col in ["date","ticker","operation","stock_price","amount","quantity","fees"]}
        for t in transactions:
            price = tickers_prices.at[t["date"], t["ticker"]]
            data["date"].append(t["date"])
            data["ticker"].append(t["ticker"])
            data["operation"].append(t["operation"])
            data["stock_price"].append(price)
            data["amount"].append(t["amount"])
            data["quantity"].append(t["amount"]/price)
            data["fees"].append(0.0)
        df = pd.DataFrame(data).set_index("date").sort_index()
        return df

    @staticmethod
    def _replicate_transactions(portfolio: list, transactions: pd.DataFrame, tickers_prices: pd.DataFrame) -> pd.DataFrame:
        """Réplique les transactions buy/sell/interest pour chaque ticker du portefeuille."""
        transactions_filtered = transactions[transactions["operation"].isin(["buy","sell","interest"])]
        data = {col: [] for col in ["date","ticker","operation","stock_price","amount","quantity","fees"]}

        for date, row in transactions_filtered.iterrows():
            if row["operation"] in ["buy","sell"]:
                for ticker, pct in portfolio[0].items():
                    price = tickers_prices.at[date, ticker]
                    amount = (row["amount"] - row["fees"]) * pct / 100 if row["operation"] == "buy" else row["amount"]/len(portfolio[0])
                    data["date"].append(date)
                    data["ticker"].append(ticker)
                    data["operation"].append(row["operation"])
                    data["stock_price"].append(price)
                    data["amount"].append(amount)
                    data["quantity"].append(amount/price)
                    data["fees"].append(0.0)
            elif row["operation"] == "interest":
                data["date"].append(date)
                data["ticker"].append(None)
                data["operation"].append("interest")
                data["stock_price"].append(None)
                data["amount"].append(row["amount"])
                data["quantity"].append(None)
                data["fees"].append(0.0)

        df = pd.DataFrame(data).set_index("date").sort_index()
        return df
