from .base_Portfolio import BasePortfolio

import pandas as pd
from datetime import datetime

class DollarCostValue(BasePortfolio):
    
    def dcv(self):
        """
        Cette méthode permet de simuler un investissement en Dollar-Cost Value ou Dynamic Cost Averaging (DCV) 
        en fonction de différents portefeuilles sur différentes plages de date.

        Explication :
            Cette méthode d’investissement est similaire au Dollar-Cost Averaging (DCA),
            mais avec une différence clé : au lieu d’investir des montants fixes à intervalles réguliers,
            l’investissement est ajusté dynamiquement pour maintenir des pourcentages cibles du portefeuille.
        """

        tickers_prices = self.tickers_prices.copy()
        investment_dates = self.get_dca_dcv_investment_dates()

        for portfolio in self.portfolio_percentage:
            portfolio_name = portfolio[-1] + " DCV"
            tickers = [ticker for ticker in portfolio[0].keys()]
            filtered_tickers_prices = tickers_prices.loc[:, tickers_prices.columns.intersection(tickers)]
            investment_dates_prices = {date: (self.initial_investment_amount() / len(investment_dates)) for date in investment_dates}

            invested_amounts_tickers, cumulative_invested_amounts = self.calculate_weighted_average_purchase_price_dcv(
                investment_dates_prices, filtered_tickers_prices, portfolio[0]
            )

            # Calcul des montants
            invested_amounts_evolution_tickers, gains_losses_evolution_tickers = self.calculate_compounded_gains_losses(
                invested_amounts_tickers, filtered_tickers_prices
            )
            invested_amounts_evolution_portfolio = invested_amounts_evolution_tickers.sum(axis=1)
            gains_losses_evolution_portfolio = gains_losses_evolution_tickers.sum(axis=1)

            # Calcul des pourcentages
            percentage_evolution_tickers = self.calculate_percentage_evolution_tickers(
                invested_amounts_evolution_tickers, cumulative_invested_amounts
            )
            percentage_evolution_portfolio = self.calculate_percentage_evolution_portfolio(
                gains_losses_evolution_portfolio, cumulative_invested_amounts.iloc[-1].sum()
            )

            # On stocke les DataFrames
            self.portfolio_twr[portfolio_name] = percentage_evolution_portfolio
            self.net_price_portfolio[portfolio_name] = gains_losses_evolution_portfolio
            self.tickers_twr[portfolio_name] = percentage_evolution_tickers
            self.net_price_tickers[portfolio_name] = gains_losses_evolution_tickers
            self.gross_price_tickers[portfolio_name] = invested_amounts_evolution_tickers
            self.dividends_tickers[portfolio_name] = self.calculate_dividend_evolution_portfolio(
                invested_amounts_evolution_tickers, filtered_tickers_prices
            )
            self.monthly_percentage_portfolio[portfolio_name] = self.calculate_monthly_percentage_evolution(
                invested_amounts_evolution_portfolio, investment_dates_prices, {}
            )
            self.fifo_price_tickers[portfolio_name] = self.calculate_fifo_price_tickers(invested_amounts_tickers)
            self.invested_funds_tickers[portfolio_name] = cumulative_invested_amounts
            self.invested_amounts_tickers[portfolio_name] = invested_amounts_tickers
            self.sold_amounts_tickers[portfolio_name] = pd.DataFrame(index=filtered_tickers_prices.index, 
                                                                    columns=filtered_tickers_prices.columns, dtype=float)
            self.bank_account_balance[portfolio_name] = invested_amounts_evolution_portfolio
            self.cash[portfolio_name] = pd.Series(0.0, index=tickers_prices.index, dtype=float)

    def calculate_weighted_average_purchase_price_dcv(
        self, investment_dates_prices: dict, tickers_prices: pd.DataFrame, tickers_percentages: dict
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Calcule le prix moyen pondéré d'achat en utilisant la méthode Dollar Cost Value.

        Args:
            investment_dates_prices (dict): Un dictionnaire où les clés sont des dates (datetime) et 
                                            les valeurs sont des montants investis (int ou float).
            tickers_prices (pd.DataFrame): Un DataFrame contenant les prix des tickers avec les dates en index et les tickers en colonnes.
            tickers_percentages (dict): Un dictionnaire avec les pourcentages alloués à chaque ticker.

        Returns:
            tuple[pd.DataFrame, pd.DataFrame]: Un tuple contenant deux DataFrames :
                - Le premier DataFrame représente les montants investis pour chaque ticker à chaque date.
                - Le deuxième DataFrame représente les montants investis cumulés pour chaque ticker à chaque date.
        """
        assert isinstance(investment_dates_prices, dict), "investment_dates_prices doit être un dictionnaire."
        assert all(isinstance(date, datetime) for date in investment_dates_prices.keys()), \
            "Les clés de investment_dates_prices doivent être des instances datetime."
        assert all(isinstance(amount, (int, float)) for amount in investment_dates_prices.values()), \
            "Les valeurs de investment_dates_prices doivent être des nombres (int ou float)."

        assert isinstance(tickers_prices, pd.DataFrame), "tickers_prices doit être un DataFrame."
        assert isinstance(tickers_percentages, dict), "tickers_percentages doit être un dictionnaire."

        invested_amounts = pd.DataFrame(0.0, index=tickers_prices.index, columns=tickers_prices.columns, dtype=float)
        cumulative_invested_amounts = pd.DataFrame(0.0, index=tickers_prices.index, columns=tickers_prices.columns, dtype=float)

        sorted_investment_dates = sorted(investment_dates_prices.keys())
        first_investment_date = min(sorted_investment_dates)

        for idx, (date, amount) in enumerate(investment_dates_prices.items()):
            if date in tickers_prices.index:
                if idx == 0:
                    # Si c'est la première fois qu'on ajoute de l'argent, on répartit selon les pourcentages de chaque ticker
                    for ticker in tickers_prices.columns:
                        added_amount_ticker = (amount * tickers_percentages[ticker] / 100)
                        invested_amounts.at[date, ticker] = added_amount_ticker
                        cumulative_invested_amounts.at[date, ticker] = added_amount_ticker
                else:
                    # Ajustement dynamique pour maintenir les pourcentages cibles
                    last_investment_date = sorted_investment_dates[idx - 1] if idx >= 1 else first_investment_date

                    invested_amounts_evolution, _ = self.calculate_compounded_gains_losses(
                        invested_amounts.loc[last_investment_date:date], tickers_prices
                    )
                    current_amounts_tickers = invested_amounts_evolution.iloc[-2]

                    # Ajustement des investissements pour respecter les pourcentages cibles
                    future_investment_amounts_tickers = self.adjust_target_investment(tickers_percentages, amount, current_amounts_tickers)

                    # Mise à jour des montants investis
                    for ticker in tickers_prices.columns:
                        cumulative_invested_amounts.at[date, ticker] = future_investment_amounts_tickers[ticker]
                        invested_amounts.at[date, ticker] = future_investment_amounts_tickers[ticker]

                    invested_amounts.loc[date] += current_amounts_tickers

        return cumulative_invested_amounts, cumulative_invested_amounts.cumsum()

    @staticmethod
    def adjust_target_investment(portfolio_allocation: dict, investment_amount: float, current_prices: pd.Series) -> dict:
        """
        Calcule combien d'argent doit être ajouté à chaque entreprise pour atteindre la répartition cible.

        Args:
            portfolio_allocation (dict): Dictionnaire avec les tickers comme clés et les pourcentages cibles comme valeurs.
            investment_amount (float): Montant total supplémentaire à investir.
            current_prices (pd.Series): Series avec les tickers comme index et les valeurs actuelles du portefeuille.

        Returns:
            dict: Dictionnaire avec les tickers comme clés et le montant à investir pour chaque entreprise.
        """
        assert isinstance(portfolio_allocation, dict), "portfolio_allocation doit être un dictionnaire"
        assert round(sum(portfolio_allocation.values())) == 100, "Les pourcentages de portfolio_allocation doivent totaliser 100"
        assert isinstance(investment_amount, (int, float)), "investment_amount doit être un nombre"
        assert isinstance(current_prices, pd.Series), "current_prices doit être un pd.Series"

        total_value = current_prices.sum() + investment_amount
        target_amounts = {ticker: (percentage / 100) * total_value for ticker, percentage in portfolio_allocation.items()}
        
        return {ticker: max(0, target_amounts[ticker] - current_prices.get(ticker, 0)) for ticker in portfolio_allocation}

