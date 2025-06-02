import json
from typing import Any

import pandas as pd

from backend.api.models import PortfolioPerformance

class PortfolioPerformanceDeserializer:
    def __init__(self, instance):
        self.instance = instance

    @staticmethod
    def _deserialize_simple_dataframe(json_str: str | dict) -> pd.DataFrame:
        if isinstance(json_str, str):
            data = json.loads(json_str)
        else:
            data = json_str

        df = pd.DataFrame.from_dict(data, orient="index")
        df.index = pd.to_datetime(df.index, errors="coerce")
        return df

    @staticmethod
    def _deserialize_nested_dataframes_dict(json_str: str | dict) -> dict[str, pd.DataFrame]:
        if isinstance(json_str, str):
            raw_dict = json.loads(json_str)
        else:
            raw_dict = json_str

        restored = {}
        for portfolio_name, tickers_dict in raw_dict.items():
            ticker_dfs = {}
            for ticker, df_dict in tickers_dict.items():
                df = pd.DataFrame(df_dict)
                df.columns = pd.to_datetime(df.columns, errors="coerce")
                df.index = pd.to_datetime(df.index, errors="coerce")

                # Si une seule colonne, on renomme avec le ticker
                if df.shape[1] == 1:
                    df.columns = [ticker]

                ticker_dfs[ticker] = df

            # Concatène les DataFrame de tous les tickers en colonnes
            portfolio_df = pd.concat(ticker_dfs.values(), axis=1)
            restored[portfolio_name] = portfolio_df

        return restored

    def load_all(self) -> dict[str, Any]:
        return {
            "twr_by_ticker": self._deserialize_nested_dataframes_dict(self.instance.twr_by_ticker),
            "net_price_by_ticker": self._deserialize_nested_dataframes_dict(self.instance.net_price_by_ticker),
            "gross_price_by_ticker": self._deserialize_nested_dataframes_dict(self.instance.gross_price_by_ticker),
            "invested_by_ticker": self._deserialize_nested_dataframes_dict(self.instance.invested_by_ticker),
            "sold_by_ticker": self._deserialize_nested_dataframes_dict(self.instance.sold_by_ticker),
            "dividends_by_ticker": self._deserialize_nested_dataframes_dict(self.instance.dividends_by_ticker),

            "portfolio_twr": self._deserialize_simple_dataframe(self.instance.portfolio_twr),
            "net_portfolio_price": self._deserialize_simple_dataframe(self.instance.net_portfolio_price),
            "monthly_percentage": self._deserialize_simple_dataframe(self.instance.monthly_percentage),
            "bank_balance": self._deserialize_simple_dataframe(self.instance.bank_balance),
            "total_invested": self._deserialize_simple_dataframe(self.instance.total_invested),
            "cash": self._deserialize_simple_dataframe(self.instance.cash),
        }



# Récupère une instance du modèle
instance = PortfolioPerformance.objects.get(user_id=1, portfolio_id=1)

# Désérialise tout
deserializer = PortfolioPerformanceDeserializer(instance)
data = deserializer.load_all()

# Exemple d'accès
portfolio_twr_df = data["portfolio_twr"]
twr_by_ticker_dict = data["invested_by_ticker"]

print(twr_by_ticker_dict)