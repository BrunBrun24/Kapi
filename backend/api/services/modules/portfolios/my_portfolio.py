from .base_portfolio import BasePortfolio

import pandas as pd

class MyPortfolio(BasePortfolio):

    def my_portfolio(self, portfolio_name: str):

        # Tickers
        ticker_invested_amounts = self.tickers_investment_amount_evolution(self.transactions)
        tickers_pru = self.calculate_pru(self.transactions, ticker_invested_amounts)
        tickers_valuation, tickers_gain_pct, tickers_gain = self.capital_gain_losses_composed(ticker_invested_amounts, tickers_pru, self.tickers_prices)

        # Portefeuille
        portfolio_valuation = tickers_valuation.sum(axis=1)
        portfolio_realized_gains_losses = self.compute_plus_value_evolution(self.transactions, ticker_invested_amounts)["plus_value_cumulative"]
        portfolio_gain = tickers_gain.sum(axis=1) + portfolio_realized_gains_losses
        # L'argent investi correspond à l'argent investi dans les tickers en enlevant les plus et moins values réalisées
        invested_money = (ticker_invested_amounts.sum(axis=1).iloc[-1] - portfolio_realized_gains_losses.iloc[-1])
        portfolio_gain_pct = self.calculate_portfolio_percentage_change(portfolio_gain, invested_money)
        

        self.tickers_twr[portfolio_name] = tickers_gain_pct
        self.tickers_gain[portfolio_name] = tickers_gain
        self.tickers_valuation[portfolio_name] = tickers_valuation
        self.tickers_dividends[portfolio_name] = self.calculate_dividends()
        self.ticker_invested_amounts[portfolio_name] = ticker_invested_amounts
        self.tickers_pru[portfolio_name] = tickers_pru

        self.portfolio_twr[portfolio_name] = portfolio_gain_pct
        self.portfolio_gain[portfolio_name] = portfolio_gain
        self.portfolio_valuation[portfolio_name] = portfolio_valuation
        self.portfolio_invested_amounts[portfolio_name] = ticker_invested_amounts.sum(axis=1)
        self.portfolio_monthly_percentages[portfolio_name] = self.calculate_monthly_percentage_change(
            portfolio_valuation,
            self.transactions
        )
        self.portfolio_cagr[portfolio_name] = self.calculate_portfolio_cagr(portfolio_valuation)
        self.portfolio_cash[portfolio_name] = self.compute_cash_evolution(self.transactions)["cash_cumulative"]
        self.portfolio_fees[portfolio_name] = self.compute_fees_evolution(self.transactions)["cumulative_fees"]
        self.portfolio_dividend_yield[portfolio_name] = self.calculate_dividend_yield(self.transactions, portfolio_valuation)
        self.portfolio_dividend_earn[portfolio_name] = self.calculate_dividend_earn(self.transactions)

        # instance à utiliser pour calculer les autres types investissement en sachant l'argent investi depuis le début
        self.money = self.initial_invested_amount(self.transactions, ticker_invested_amounts)

        # print(self.calculate_portfolio_cagr(portfolio_valuation))
        # print(self.calculate_portfolio_sharpe_ratio(portfolio_gain, 0.025, "journalier"))
        # print(self.calculate_portfolio_sortino_ratio(portfolio_gain))
        # print(self.calculate_ecart_type(portfolio_valuation))

        # print(self.calculer_drawdown_max(portfolio_valuation))
        # print(self.calculer_drawdown_max_un_jour(portfolio_valuation))


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

        # graphique(ticker_invested_amounts, "Argent investis cumulées")
        # graphique(tickers_gain, "Gains €")
        # graphique(tickers_gain_pct, "TWR")
        # graphique(tickers_valuation, "Valorisation")
        # graphique(tickers_pru, "PRU tickers")
        # graphique(self.calculate_dividends(), "Dividendes par tickers")
        # graphique(self.compute_cash_evolution(self.transactions)["cash_cumulative"], "Cash")

        # graphique(portfolio_valuation, " Valorisation du portefeuille")
        # graphique(portfolio_gain, "Portefeuille €")
        # graphique(portfolio_gain_pct, "Portefeuille %")
        
        # graphique(self.compute_cash_evolution(self.transactions), "cash") # A REVOIR ERREUR contenue en négatif (IMPOSSIBLE)


    def compute_cash_evolution(self, transactions_df: pd.DataFrame) -> pd.DataFrame:
        """
        Calcule l’évolution journalière du cash du portefeuille à partir des
        transactions, en tenant compte des achats, ventes, dépôts, retraits,
        dividendes et intérêts, sur toute la période spécifiée.

        Le résultat contient deux séries :
        - les flux journaliers de cash ;
        - le cash cumulé jour après jour.

        Parameters
        ----------
        transactions_df : pd.DataFrame
            DataFrame indexé par date, contenant au minimum les colonnes :
            - `'operation'` : type d’opération (e.g. `'buy'`, `'sell'`, `'deposit'`, etc.)
            - `'amount'` : montant brut de l’opération
            - `'fees'` : frais associés à la transaction

        Returns
        -------
        pd.DataFrame
            DataFrame indexé par date (`DatetimeIndex` quotidien) avec deux colonnes :
            - `'cash_flow'` : flux net de cash pour chaque jour (somme des opérations)
            - `'cash_cumulative'` : cumul des flux de cash depuis le début de la période
        """

        def calculate_cash_flow(row):
            operation = row['operation']
            amount = row['amount']
            fees = row['fees']

            if operation == 'buy':
                return -(amount + fees)
            elif operation == 'sell':
                return amount - fees
            elif operation in ['deposit', 'dividend', 'interest']:
                return (amount - fees)
            elif operation == 'withdrawal':
                return -amount
            else:
                return 0

        # Assure-toi que l'index est datetime
        transactions_df.index = pd.to_datetime(transactions_df.index)

        # Calcul du cash flow par transaction
        transactions_df['cash_flow'] = transactions_df.apply(calculate_cash_flow, axis=1)

        # Somme des cash flows par date (l'index)
        cash_by_date = transactions_df['cash_flow'].groupby(transactions_df.index).sum()

        # Création de l'index complet de dates
        full_date_index = pd.date_range(start=self.start_date, end=self.end_date, freq='D')

        # Réindexer pour avoir toutes les dates, remplissage des NaN par 0
        cash_by_date = cash_by_date.reindex(full_date_index, fill_value=0)

        # Calcul cumulatif du cash
        cash_cumulative = cash_by_date.cumsum()

        # Création du DataFrame final
        result_df = pd.DataFrame({
            'cash_flow': cash_by_date,
            'cash_cumulative': cash_cumulative
        })

        result_df.index.name = 'index'

        return result_df

    def calculate_dividends(self) -> pd.DataFrame:
        """
        Calcule les dividendes nets (dividende - frais) reçus pour chaque ticker,
        sur toute la période du portefeuille, et les organise par date.

        Cette méthode :
        - filtre les opérations de type `'dividend'` dans le portefeuille ;
        - agrège les montants nets (après frais) par date et par ticker ;
        - retourne un DataFrame quotidien contenant les dividendes reçus.

        Returns
        -------
        pd.DataFrame
            DataFrame indexé par date (`DatetimeIndex`) avec :
            - colonnes = tickers pour lesquels des dividendes ont été versés ;
            - valeurs = montant net du dividende reçu ce jour-là (0.0 si aucun).
        """

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

    def compute_fees_evolution(self, transactions_df: pd.DataFrame) -> pd.DataFrame:
        """
        Calcule l'évolution quotidienne des frais de transaction sur toute la période
        du portefeuille, ainsi que leur cumul.

        Cette méthode :
        - agrège les frais journaliers à partir des opérations financières ;
        - remplit les jours sans transactions avec zéro ;
        - calcule les frais cumulés jour après jour.

        Parameters
        ----------
        transactions_df : pd.DataFrame
            DataFrame indexé par date contenant une colonne `'fees'` représentant
            les frais associés à chaque transaction.

        Returns
        -------
        pd.DataFrame
            DataFrame indexé par date (`DatetimeIndex`) avec deux colonnes :
            - `'daily_fees'` : total des frais facturés pour chaque jour ;
            - `'cumulative_fees'` : somme cumulée des frais depuis `self.start_date`.
        """

        # 1) Créer l’index journalier de référence
        date_range = pd.date_range(start=self.start_date, end=self.end_date, freq='D')

        # 2) Frais journaliers (0 € pour les jours sans opération)
        daily_fees = (
            transactions_df['fees']     # on ne garde que la colonne 'fees'
            .resample('D')              # agrégation quotidienne
            .sum()                      # si plusieurs lignes le même jour
            .reindex(date_range, fill_value=0.0)  # complétion des dates manquantes
        )

        # 3) Mettre en DataFrame et ajouter la cumulative
        fees_evolution_df = daily_fees.to_frame(name='daily_fees')
        fees_evolution_df['cumulative_fees'] = fees_evolution_df['daily_fees'].cumsum()

        return fees_evolution_df
