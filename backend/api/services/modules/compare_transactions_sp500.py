from decimal import Decimal
import pandas as pd
from datetime import datetime
from api.models import PortfolioTicker, PortfolioTransaction, StockPrice, TickerPerformanceCompareSP500, TransactionCompareSP500
from api.services.modules.portfolios.compute_portfolio_performance import ComputePortfolioPerformance

from api.services.modules.portfolios.base_portfolio import BasePortfolio

class ComparePortfolioSP500():
    def __init__(self, user, portfolios):
        self.user = user
        self.portfolio_engine = ComputePortfolioPerformance()
        self.ticker_sp500 = "SPY"

        self.compare_transactions_sp500 = pd.DataFrame(columns=self._get_transaction_columns())
        self.compare_tickers_sp500 = pd.DataFrame(columns=self._get_ticker_columns())

        for portfolio in portfolios:
            self._init_performance(portfolio, per_ticker=False)
            self._init_performance(portfolio, per_ticker=True)

    def _get_transaction_columns(self):
        return [
            "ticker", "date", "purchase_amount", "value_ticker",
            "gains", "gains_%", "sp500", "sp500_%", "gap", "duration",
            "%_an", "amount", "yield", "quantity", "stock_price", "fees", "currency"
        ]

    def _get_ticker_columns(self):
        return [
            "ticker", "number_of_transaction", "purchase_amount", "value_ticker",
            "gains", "gains_%", "sp500", "sp500_%", "gap", "duration",
            "%_an", "amount", "yield", "quantity", "fees", "currency"
        ]

    def _get_aligned_prices(self):
        tickers_prices = StockPrice.get_open_prices_dataframe_for_user(self.user.id)
        sp500_prices = StockPrice.get_open_prices_dataframe_for_ticker(self.ticker_sp500)

        tickers_prices = tickers_prices.reindex(
            pd.date_range(start=tickers_prices.index[0], end=tickers_prices.index[-1], freq='D')
        ).ffill().bfill()

        sp500_prices = sp500_prices.reindex(
            pd.date_range(start=sp500_prices.index[0], end=sp500_prices.index[-1], freq='D')
        ).ffill().bfill()

        return tickers_prices, sp500_prices

    def _init_performance(self, portfolio, per_ticker=False):
        tickers_prices, sp500_prices = self._get_aligned_prices()

        if per_ticker:
            transactions_dict = PortfolioTransaction.get_open_positions_dict(self.user.id, portfolio)
            for ticker, transactions in transactions_dict.items():
                self._process_transactions(portfolio, transactions, ticker, tickers_prices, sp500_prices, aggregated=True)
        else:
            transactions = PortfolioTransaction.get_buy_transactions(self.user.id, portfolio)
            for idx in range(len(transactions)):
                tr = transactions.iloc[[idx]]
                self._process_transactions(portfolio, tr, tr["ticker"].iloc[0], tickers_prices, sp500_prices, aggregated=False)

    def _transaction_sp500(self, transaction_ticker: pd.DataFrame, start_date: datetime) -> pd.DataFrame:
        tr = transaction_ticker.copy(deep=True)
        tr["ticker"] = self.ticker_sp500
        tr["stock_price"] = StockPrice.get_price_on_date(self.ticker_sp500, start_date, transaction_ticker["currency"].iloc[0])
        tr["quantity"] = transaction_ticker["amount"] / transaction_ticker["stock_price"]

        return tr

    def _transaction_per_ticker_sp500(self, transactions: pd.DataFrame) -> pd.DataFrame:
        """
        Construit un DataFrame de transactions fictives pour le S&P500
        à partir des transactions réelles d’un ticker.

        Args:
            transactions (pd.DataFrame): DataFrame des transactions réelles (colonnes : amount, currency, stock_price, ...)
            start_date (datetime): Date de début de la transaction

        Returns:
            pd.DataFrame: DataFrame des transactions S&P500 équivalentes
        """
        transactions_sp500 = pd.DataFrame()

        for idx, row in transactions.iterrows():
            stock_price = StockPrice.get_price_on_date(self.ticker_sp500, idx, row["currency"])
            quantity = row["amount"] / stock_price

            transactions_sp500 = pd.concat([
                transactions_sp500,
                pd.DataFrame(
                    {
                        "ticker": [self.ticker_sp500],
                        "stock_price": [stock_price],
                        "quantity": [quantity],
                        "amount": [row["amount"]],
                        "currency": [row["currency"]],
                        "operation": [row["operation"]],
                    },
                    index=[idx]
                )
            ])

        return transactions_sp500

    def _process_transactions(self, portfolio, transactions, ticker, tickers_prices, sp500_prices, aggregated=False):
        start_date = pd.to_datetime(transactions.index[0]).normalize()
        end_date = tickers_prices.index[-1]

        ticker_prices = tickers_prices[ticker].loc[start_date:end_date].to_frame(name=ticker)
        ticker_prices_convert = StockPrice.convert_dataframe_to_currency(ticker_prices, transactions["currency"].iloc[0])
        performances_ticker = self.portfolio_engine.compute_portfolio_performance(transactions, ticker_prices_convert, start_date, end_date)

        base_portfolio = BasePortfolio(start_date, end_date)
        performances_ticker["portfolio_dividend_earn"] = base_portfolio.calculate_dividends_evolution(
            performances_ticker["tickers_valuation"], ticker_prices
        ).sum(axis=0).iloc[-1]
        performances_ticker["portfolio_dividend_yield"] = (
            performances_ticker["portfolio_dividend_earn"] /
            performances_ticker["tickers_valuation"].at[end_date, ticker]
        ) * 100

        if aggregated:
            tr_sp500 = self._transaction_per_ticker_sp500(transactions)
        else:
            tr_sp500 = self._transaction_sp500(transactions, start_date)

        sp500_prices_convert = StockPrice.convert_dataframe_to_currency(sp500_prices.loc[start_date:end_date], transactions["currency"].iloc[0])
        performances_sp500 = self.portfolio_engine.compute_portfolio_performance(tr_sp500, sp500_prices_convert, start_date, end_date)

        self._save_transaction_to_db(portfolio, transactions, performances_ticker, performances_sp500, ticker, end_date, aggregated)

    def _save_transaction_to_db(self, portfolio, transactions, performances_ticker, performances_sp500, ticker, end_date, aggregated=False):
        portfolio_ticker_instance = PortfolioTicker.objects.get(
            portfolio=portfolio,
            ticker__ticker=ticker
        )

        def to_decimal(value):
            """Convertit les valeurs en Decimal, même si ce sont des float ou numpy types."""
            return Decimal(str(value)) if value is not None else None
        
        years = len(performances_ticker["tickers_twr"].index) / 365
        annualized_return = round(((
            performances_ticker["tickers_valuation"].at[end_date, ticker] 
            / performances_ticker["tickers_invested_amounts"].at[end_date, ticker]
        ) ** (1 / years) - 1) * 100, 2)

        if aggregated:
            TickerPerformanceCompareSP500.create_or_update_transaction(
                user=self.user,
                portfolio=portfolio,
                ticker=portfolio_ticker_instance,
                number_of_transactions=to_decimal(len(transactions)),
                purchase_amount=to_decimal(transactions["amount"].sum()),
                current_value=to_decimal(performances_ticker["tickers_valuation"].at[end_date, ticker]),
                total_gain=to_decimal(performances_ticker["tickers_gain"].at[end_date, ticker]),
                gain_percentage=to_decimal(performances_ticker["tickers_twr"].at[end_date, ticker]),
                sp500_value=to_decimal(performances_sp500["tickers_gain"].at[end_date, self.ticker_sp500]),
                sp500_gain_percentage=to_decimal(performances_sp500["tickers_twr"].at[end_date, self.ticker_sp500]),
                performance_gap=to_decimal(performances_ticker["tickers_twr"].at[end_date, ticker] - performances_sp500["tickers_twr"].at[end_date, self.ticker_sp500]),
                holding_duration=to_decimal(len(performances_ticker["tickers_twr"].index)),
                annualized_return=to_decimal(annualized_return),
                dividend_amount=to_decimal(performances_ticker["portfolio_dividend_earn"]),
                dividend_yield=to_decimal(performances_ticker["portfolio_dividend_yield"]),
                quantity=to_decimal(transactions["quantity"].sum()),
                transaction_fees=to_decimal(transactions["fees"].sum()),
                currency=transactions["currency"].iloc[-1]
            )
        else:
            for idx, row in transactions.iterrows():
                TransactionCompareSP500.create_or_update_transaction(
                    user=self.user,
                    portfolio=portfolio,
                    ticker=portfolio_ticker_instance,
                    date=row.name,
                    purchase_amount=to_decimal(row["amount"]),
                    current_value=to_decimal(performances_ticker["tickers_valuation"].at[end_date, ticker]),
                    total_gain=to_decimal(performances_ticker["tickers_gain"].at[end_date, ticker]),
                    gain_percentage=to_decimal(performances_ticker["tickers_twr"].at[end_date, ticker]),
                    sp500_value=to_decimal(performances_sp500["tickers_gain"].at[end_date, self.ticker_sp500]),
                    sp500_gain_percentage=to_decimal(performances_sp500["tickers_twr"].at[end_date, self.ticker_sp500]),
                    performance_gap=to_decimal(performances_ticker["tickers_twr"].at[end_date, ticker] - performances_sp500["tickers_twr"].at[end_date, self.ticker_sp500]),
                    holding_duration=to_decimal(len(performances_ticker["tickers_twr"].index)),
                    annualized_return=to_decimal(annualized_return),
                    dividend_amount=to_decimal(performances_ticker["portfolio_dividend_earn"]),
                    dividend_yield=to_decimal(performances_ticker["portfolio_dividend_yield"]),
                    quantity=to_decimal(row["quantity"]),
                    stock_price=to_decimal(row["stock_price"]),
                    transaction_fees=to_decimal(row["fees"]),
                    currency=row["currency"]
                )
