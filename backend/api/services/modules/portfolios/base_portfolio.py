import yfinance as yf
import pandas as pd
from datetime import timedelta

class BasePortfolio:

    ########## Pourcentage ##########
    @staticmethod
    def calculate_monthly_percentage_change(portfolio_series: pd.Series, transactions_df: pd.DataFrame) -> pd.Series:
        """
        Calcule l'évolution mensuelle en pourcentage du portefeuille :
        - Si des ventes existent, les apports sont corrigés (stratégie active)
        - Sinon, les apports ne sont pas corrigés (stratégie passive / DCA)
        
        Args:
            portfolio_series (pd.Series): Valeur quotidienne du portefeuille (index = dates)
            transactions_df (pd.DataFrame): Données des transactions contenant 'operation' et 'amount'
        
        Returns:
            pd.Series: Série mensuelle d'évolution en pourcentage (index = YYYY-MM)
        """
        # Conversion des index en datetime
        portfolio_series.index = pd.to_datetime(portfolio_series.index)
        transactions_df = transactions_df.copy()
        transactions_df.index = pd.to_datetime(transactions_df.index)

        # ❌ Supprimer les valeurs nulles ou égales à 0
        portfolio_series = portfolio_series[portfolio_series > 0].dropna()
        # Récupération des valeurs de début et fin de mois (inclut les mois partiels)
        monthly_start = portfolio_series.resample("ME").first()
        monthly_end = portfolio_series.resample("ME").last()

        # Vérifie s'il y a des ventes
        has_sales = "sell" in transactions_df["operation"].unique()

        if has_sales:
            # Ajout d'une colonne 'amount' avec valeurs négatives pour les ventes
            transactions_df["amount"] = transactions_df["amount"].astype(float)
            transactions_df.loc[transactions_df["operation"] == "sell", "amount"] *= -1

            # Somme mensuelle des investissements nets
            monthly_net_investment = transactions_df.groupby(pd.Grouper(freq="ME"))["amount"].sum()

            # Calcul de la performance ajustée
            monthly_returns = {}
            for (compt, date) in enumerate(monthly_end.index):
                if compt != 0:
                    start_value = monthly_start.get(date, None)
                    end_value = monthly_end.get(date, None)
                    net_investment = monthly_net_investment.get(date, 0.0)

                    if start_value is None or end_value is None or start_value == 0:
                        monthly_returns[date.strftime("%Y-%m")] = float("nan")
                        continue

                    # Ajustement de la valeur de fin de mois avec les apports
                    adjusted_end_value = end_value - net_investment

                    # Calcul du rendement ajusté
                    monthly_return = ((adjusted_end_value - start_value) / start_value) * 100
                else:
                    net_investment = monthly_net_investment.get(date, 0.0)
                    end_value = monthly_end.get(date, None)
                    monthly_return = (end_value * 100 / net_investment) - 100

                monthly_returns[date.strftime("%Y-%m")] = monthly_return
        else:
            # Stratégie passive : pas d'ajustement des apports
            monthly_returns = (((monthly_end - monthly_start) / monthly_start) * 100).to_dict()
            # Conversion de l'index en chaîne pour uniformiser
            monthly_returns = {date.strftime("%Y-%m"): value for date, value in monthly_returns.items()}

        return pd.Series(monthly_returns)
    
    @staticmethod
    def calculate_percentage_evolution_tickers(invested_money_tickers_evolution: pd.DataFrame, accumulated_invested_money: pd.DataFrame) -> pd.DataFrame:
        """
        Calcule l'évolution en pourcentage de chaque ticker entre le montant investi cumulé et l'évolution globale du portefeuille.

        Args:
            invested_money_tickers_evolution (pd.DataFrame): DataFrame contenant les valeurs globales du portefeuille pour chaque ticker.
            accumulated_invested_money (pd.DataFrame): DataFrame contenant les montants investis cumulés pour chaque ticker.

        Returns:
            pd.DataFrame: DataFrame contenant l'évolution en pourcentage pour chaque ticker.
        """
        assert isinstance(invested_money_tickers_evolution, pd.DataFrame), "invested_money_tickers_evolution doit être un DataFrame"
        assert isinstance(accumulated_invested_money, pd.DataFrame), "accumulated_invested_money doit être un DataFrame"

        # Initialiser le DataFrame pour stocker l'évolution en pourcentage
        tickers_percentage_change = pd.DataFrame(index=invested_money_tickers_evolution.index, columns=invested_money_tickers_evolution.columns, dtype=float)
        tickers_percentage_change.iloc[0] = 0

        # Calcul de l'évolution en pourcentage
        for i in range(1, len(invested_money_tickers_evolution.index)):
            current_date = invested_money_tickers_evolution.index[i]

            # Calcul de l'évolution en pourcentage
            tickers_percentage_change.loc[current_date] = (
                (invested_money_tickers_evolution.loc[current_date] - accumulated_invested_money.loc[current_date]) /
                accumulated_invested_money.loc[current_date]
            ) * 100

        return tickers_percentage_change

    @staticmethod
    def calculate_portfolio_percentage_change(portfolio_profit_loss_evolution: pd.Series, invested_money: float) -> pd.Series:
        """
        Calcule l'évolution en pourcentage de la valeur totale du portefeuille par rapport à l'argent investi.

        Args:
            portfolio_profit_loss_evolution (pd.Serie): Serie contenant les valeurs globales du portefeuille, indexé par date.
            invested_money (float): Montant total investi dans le portefeuille.

        Returns:
            pd.DataFrame: DataFrame contenant l'évolution en pourcentage de la valeur totale du portefeuille par rapport à l'argent investi.
        """
        assert isinstance(portfolio_profit_loss_evolution, pd.Series), "portfolio_profit_loss_evolution doit être une Serie"
        assert isinstance(invested_money, (int, float)), "invested_money doit être un nombre (int ou float)"
 
        # Calcul de l'évolution en pourcentage par rapport à l'argent investi
        percentage_change = (((invested_money + portfolio_profit_loss_evolution) - invested_money) / invested_money) * 100

        # Création d'un DataFrame pour retourner les résultats
        portfolio_percentage_change = pd.DataFrame(percentage_change, columns=['PercentageChange'])

        return portfolio_percentage_change
    #################################

    ########## Prix ##########
    @staticmethod
    def calculate_capital_gain_loss_composed(invested_money: pd.DataFrame, tickers_prices: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Calcule la plus-value ou moins-value quotidienne réalisée pour chaque ticker en utilisant une composition 
        des gains/pertes à partir du prix d'achat initial.

        Args:
            invested_money (pd.DataFrame): DataFrame contenant les montants investis jusqu'au jour actuel, indexé par date.
            tickers_prices (pd.DataFrame): DataFrame contenant les prix quotidiens des actions, indexé par date.

        Returns:
            tuple: (pd.DataFrame, pd.DataFrame)
                - pd.DataFrame: DataFrame avec les dates en index et les tickers en colonnes, contenant la valeur globale 
                                d'investissement composée au fil des jours pour chaque action.
                - pd.DataFrame: DataFrame avec les dates en index et les tickers en colonnes, contenant la plus-value ou 
                                moins-value composée au fil des jours pour chaque action.
        """
        assert isinstance(invested_money, pd.DataFrame), "invested_money doit être un DataFrame"
        assert isinstance(tickers_prices, pd.DataFrame), "tickers_prices doit être un DataFrame"
        
        # Initialiser le DataFrame pour stocker les valeurs composées de plus/moins-value
        tickers_invested_money_evolution = pd.DataFrame(index=invested_money.index, columns=invested_money.columns, dtype=float)
        tickers_profit_loss_evolution = pd.DataFrame(index=invested_money.index, columns=invested_money.columns, dtype=float)

        # Calcul de la plus-value composée pour chaque jour
        for ticker in invested_money.columns:
            
            # Initialiser avec la valeur d'achat initiale pour chaque ticker
            tickers_invested_money_evolution.loc[invested_money.index[0], ticker] = invested_money.loc[invested_money.index[0], ticker]
            tickers_profit_loss_evolution.loc[invested_money.index[0], ticker] = 0

            accumulated_invested_money = invested_money.loc[invested_money.index[0], ticker]

            for i in range(1, len(invested_money.index)):
                previous_date = invested_money.index[i-1]
                current_date = invested_money.index[i]

                # Calcul de l'évolution en pourcentage entre le jour actuel et le jour précédent
                percentage_change = (tickers_prices.loc[current_date, ticker] / tickers_prices.loc[previous_date, ticker]) - 1
                
                # Calcule l'évolution globale du portefeuille
                tickers_invested_money_evolution.loc[current_date, ticker] = tickers_invested_money_evolution.loc[previous_date, ticker] * (1 + percentage_change)
                tickers_profit_loss_evolution.loc[current_date, ticker] = tickers_invested_money_evolution.loc[current_date, ticker] - accumulated_invested_money
                
                if invested_money.loc[previous_date, ticker] != invested_money.loc[current_date, ticker]:
                    tickers_invested_money_evolution.loc[current_date, ticker] += invested_money.loc[current_date, ticker]
                    accumulated_invested_money += invested_money.loc[current_date, ticker]

        return tickers_invested_money_evolution, tickers_profit_loss_evolution

    @staticmethod
    def calculate_dividends_evolution(portfolio_gross_prices_evolution: pd.DataFrame, ticker_price_df: pd.DataFrame) -> pd.DataFrame:
        """
        Calcule l'évolution des dividends pour chaque ticker d'un portefeuille, basée sur les prix bruts et les dividends distribués.

        Args:
            portfolio_gross_prices_evolution (pd.DataFrame): Évolution brute des prix des tickers.
            ticker_price_df (pd.DataFrame): Prix des tickers correspondants.

        Returns:
            pd.DataFrame: Évolution des dividends pour chaque ticker, répartis sur les dates du portefeuille.
        """
        assert isinstance(portfolio_gross_prices_evolution, pd.DataFrame), "portfolio_gross_prices_evolution doit être un DataFrame"
        assert isinstance(ticker_price_df, pd.DataFrame), "ticker_price_df doit être un DataFrame"
        assert portfolio_gross_prices_evolution.index.equals(ticker_price_df.index), "Les index des DataFrames doivent être identiques"

        # Initialisation du DataFrame des dividends
        tickers_dividends = pd.DataFrame(0, index=portfolio_gross_prices_evolution.index, columns=portfolio_gross_prices_evolution.columns, dtype=float)

        for ticker in portfolio_gross_prices_evolution.columns:
            # Récupération des dividends
            dividends = yf.Ticker(ticker).dividends

            # Suppression de la timezone si nécessaire
            dividends.index = dividends.index.tz_localize(None) if dividends.index.tz else dividends.index

            # Aligner les dividends sur l'index des prix du portefeuille
            dividends = dividends.reindex(portfolio_gross_prices_evolution.index, method='ffill').fillna(0)

            # Calculer le montant des dividends en fonction des prix
            tickers_dividends[ticker] = round(dividends * portfolio_gross_prices_evolution[ticker] / ticker_price_df[ticker], 2)

        return tickers_dividends
    
    def calculate_fifo_purchase_price_for_tickers(self, invested_amounts: pd.DataFrame) -> pd.DataFrame:
        """
        Calculates the average purchase price (FIFO) for each stock based on the invested amounts and ticker prices.

        Args:
            invested_amounts (pd.DataFrame): DataFrame containing the invested amounts for each stock in columns,
                                            with dates as the index.

        Returns:
            pd.DataFrame: DataFrame containing the average purchase prices (FIFO) for each stock.
        """
        assert isinstance(invested_amounts, pd.DataFrame), "invested_amounts must be a DataFrame"

        # Data cleaning: keep only the rows where the invested amounts are not all zero
        invested_amounts = invested_amounts.loc[invested_amounts.sum(axis=1) != 0]
        ticker_prices = self.ticker_prices.loc[invested_amounts.index]

        # Initialize the DataFrame to store FIFO prices
        fifo_prices = pd.DataFrame(index=invested_amounts.index, columns=invested_amounts.columns, dtype=float)

        # Loop over each ticker to calculate the average purchase price
        for ticker in invested_amounts.columns:
            amounts = invested_amounts[ticker]
            prices = ticker_prices[ticker]
            
            total_quantity = 0
            total_invested = 0
            
            for date in amounts.index:
                invested_amount = amounts[date]
                daily_price = prices[date]
                
                if invested_amount > 0:  # Investment made on this day
                    quantity_purchased = invested_amount / daily_price
                    total_quantity += quantity_purchased
                    total_invested += invested_amount

                # Calculate the FIFO average price if there is a total quantity
                fifo_prices.loc[date, ticker] = total_invested / total_quantity if total_quantity > 0 else 0

        # Fill the missing dates between startDate and endDate
        date_range = pd.date_range(start=self.start_date, end=self.end_date, freq='D')
        fifo_prices = fifo_prices.reindex(date_range)  # Add missing dates
        fifo_prices = fifo_prices.ffill()  # Forward fill the latest available values
        first_investment_date = invested_amounts.index.min() - timedelta(days=1)
        fifo_prices.loc[:first_investment_date] = 0

        return fifo_prices
    ##########################
