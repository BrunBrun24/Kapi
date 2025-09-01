import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from api.models import Dividend

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
            monthly_returns = pd.Series(index=monthly_start.index)
            fisrt_month = True

            for date in monthly_start.index:
                month_start = date.replace(day=1)
                month_end = month_start + pd.offsets.MonthEnd(0)

                money_add = transactions_df.loc[
                    (transactions_df["operation"] == "buy") &
                    (transactions_df.index >= month_start) &
                    (transactions_df.index <= month_end)
                ].copy()
                # Conversion en float si nécessaire
                money_add["amount"] = money_add["amount"].astype(float)
                money_add["fees"] = money_add["fees"].astype(float)
                # Calcul de l’investissement net : montant - frais
                monthly_net_buy = (money_add["amount"] - money_add["fees"]).sum()
                if fisrt_month:
                    monthly_net_buy -= money_add["amount"].iloc[0]
                    fisrt_month = False

                money_sell = transactions_df.loc[
                    (transactions_df["operation"] == "sell") &
                    (transactions_df.index >= month_start) &
                    (transactions_df.index <= month_end)
                ].copy()
                # Conversion en float si nécessaire
                money_sell["amount"] = money_sell["amount"].astype(float)
                # Calcul de l’investissement net : montant - frais
                monthly_net_sell = (money_sell["amount"]).sum()

                start_val = monthly_start.get(date, None)
                end_val = monthly_end.get(date, None)

                if pd.isna(start_val) or pd.isna(end_val) or (start_val + monthly_net_buy) == 0:
                    monthly_returns[date] = float("nan")
                else:
                    monthly_returns[date] = ((end_val / (start_val + monthly_net_buy - monthly_net_sell)) - 1) * 100

            return monthly_returns
        else:
            # Stratégie passive : pas d'ajustement des apports
            monthly_returns = (((monthly_end - monthly_start) / monthly_start) * 100)

            return pd.Series(monthly_returns)
    
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
        percentage_change = round((((invested_money + portfolio_profit_loss_evolution) - invested_money) / invested_money) * 100, 2)

        # Création d'un DataFrame pour retourner les résultats
        portfolio_percentage_change = pd.DataFrame(percentage_change, columns=['PercentageChange'])

        return portfolio_percentage_change
    #################################


    ########## Prix ##########
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

    def download_tickers_sma(self, start_date: datetime, end_date: datetime, tickers: list, sma: list) -> pd.DataFrame:
        """
        Calcule la moyenne mobile simple (SMA) pour chaque ticker dans le DataFrame des prix des tickers
        sur une période donnée.

        Args:
            start_date (datetime): La date de début pour le calcul de la SMA.
            end_date (datetime): La date de fin pour le calcul de la SMA.
            tickers (list): Liste des symboles boursiers à télécharger.
            sma (list): Liste des périodes (en jours) pour lesquelles calculer la SMA.

        Returns:
            pd.DataFrame: DataFrame contenant les SMA calculées pour chaque période et chaque ticker.
        """
        assert isinstance(start_date, datetime), "start_date doit être un objet datetime"
        assert isinstance(end_date, datetime), "end_date doit être un objet datetime"
        assert isinstance(tickers, list) and all(isinstance(ticker, str) for ticker in tickers), "tickers doit être une liste de chaînes de caractères"
        assert isinstance(sma, list) and all(isinstance(sma_day, int) for sma_day in sma), "sma doit être une liste d'entiers"

        ticker_prices = self.download_tickers_price(tickers, (start_date - timedelta(max(sma) + 50)), end_date)
        sma_df = pd.DataFrame()  # Initialiser avec les mêmes index que ticker_price_df

        for num_days in sma:
            # Calculer la moyenne mobile pour chaque ticker (chaque colonne de ticker_price_df)
            moving_average = ticker_prices.rolling(window=num_days).mean()
            
            # Ajouter chaque colonne SMA avec un suffixe du nombre de jours
            for col in moving_average.columns:
                sma_df[f"{col}_SMA_{num_days}"] = moving_average[col]

        return sma_df
    ##########################


    ########## Flux ##########
    def tickers_investment_amount_evolution(self, transaction_df: pd.DataFrame) -> pd.Series:
        """
        Calcule l'évolution du montant total investi dans le portefeuille au fil du temps.

        Cette fonction suit les investissements en ajoutant les montants investis aux dates d'achat 
        et en mettant à zéro les montants aux dates de vente.

        Returns:
            pd.Series: Série contenant l'évolution quotidienne du montant investi, avec les dates en index.
        """
        
        # On récupère tous les tickers achetés
        tickers_buy = transaction_df["ticker"].dropna().unique()
        # On initialise un dictionnaire pour les investissements
        date_range = pd.date_range(self.start_date, self.end_date)
        invested_amounts = pd.DataFrame(0.0, index=date_range, columns=tickers_buy)

        # Pour chaque ticker acheté
        for ticker in tickers_buy:
            ticker_operations = transaction_df[
                (transaction_df["ticker"] == ticker) &
                (transaction_df["operation"].isin(["buy", "sell"]))
            ]
            quantity_ticker = 0

            # On boucle sur chaque transaction pour ce ticker
            for date, data in ticker_operations.iterrows():
                # Si c'est une opération d'achat
                if data["operation"] == "buy":
                    invested_amounts.loc[date:, ticker] += (data["amount"])
                    quantity_ticker += data["quantity"]
                elif data["operation"] == "sell":
                    # Vente partielle ou totale, selon la quantité vendue
                    sell_quantity = data["quantity"]
                    sell_amount = (data["amount"])

                    if round(quantity_ticker, 6) > round(sell_quantity, 6):
                        # Vente partielle : on ajuste la quantité restante et l'investissement
                        new_amount = invested_amounts.loc[date, ticker] - sell_amount
                        if new_amount > 0:
                            invested_amounts.loc[date:, ticker] = new_amount
                        else:
                            invested_amounts.loc[date:, ticker] = 0.0
                    else:
                        # Vente totale : on réinitialise l'investissement à 0
                        invested_amounts.loc[date:, ticker] = 0.0

        return invested_amounts

    def initial_invested_amount(self, transactions_df: pd.DataFrame, ticker_invested_amounts: pd.DataFrame) -> float:
        """
        Calcule le capital réellement injecté dans le portefeuille.

        Règles :
        - Une vente crédite available_cash de (amount - fees)
        - Un achat débite d'abord available_cash, puis, si nécessaire,
        ajoute la différence à invested_cash.
        - invested_cash reste toujours ≥ 0.
        """
        # Sécurité : dates en datetime, tri chronologique
        tx = transactions_df.copy()
        tx.index = pd.to_datetime(tx.index)
        tx.sort_index(inplace=True)

        available_cash = 0.0   # cash issu des ventes
        money_invest = 0.0   # cash issu des ventes
        invested_cash = 0.0    # cash extérieur réellement injecté

        for date, row in tx.iterrows():
            ticker = row["ticker"]
            amount = float(row["amount"])
            fees = float(row["fees"])
            op = row["operation"]

            if op == "sell":
                # produit net de la vente
                if (amount > ticker_invested_amounts.loc[date - timedelta(days=1), ticker]):
                    money_invest += ticker_invested_amounts.loc[date - timedelta(days=1), ticker]

                available_cash += (amount - fees)
            elif op == "buy":
                cost = (amount + fees)  # coût total de l'achat
                if available_cash >= cost:
                    # on finance entièrement avec le cash dispo
                    available_cash -= cost
                else:
                    # on utilise tout le cash dispo, le reste vient de l'extérieur
                    invested_cash += cost - available_cash
                    available_cash = 0.0

                if money_invest >= cost:
                    # on finance entièrement avec le cash dispo
                    money_invest -= cost

        return (invested_cash + money_invest)

    def compute_plus_value_evolution(self, transactions_df: pd.DataFrame, ticker_invested_amounts: pd.DataFrame) -> pd.DataFrame:
        """
        Calcule l’évolution quotidienne de la plus-value réalisée, à partir des
        transactions de vente, en se basant sur les montants investis la veille.

        La méthode :
        - calcule les plus-values journalières issues des ventes uniquement ;
        - agrège ces plus-values par jour ;
        - produit un cumul journalier plafonné à 0 (pas de moins-value cumulative).

        Parameters
        ----------
        transactions_df : pd.DataFrame
            DataFrame indexé par date, contenant au minimum les colonnes suivantes :
            - `'operation'` : type d’opération (e.g. `'buy'`, `'sell'`, `'deposit'`, etc.)
            - `'amount'` : montant brut de l’opération
            - `'ticker'` : symbole de l’actif concerné

        ticker_invested_amounts : pd.DataFrame
            DataFrame indexé par date, avec pour colonnes les tickers, représentant
            le montant cumulé investi pour chaque actif à chaque date.

        Returns
        -------
        pd.DataFrame
            DataFrame indexé par date (fréquence quotidienne) avec deux colonnes :
            - `'plus_value_flow'` : plus-value nette réalisée ce jour-là (0 si aucune vente)
            - `'plus_value_cumulative'` : somme cumulée des plus-values réalisées, **plafonnée à 0 minimum**
            (on n’accumule pas de moins-value dans cette logique comptable).
        """

        def calculate_plus_value_flow(row):
            date = (row.name - timedelta(days=1))
            ticker = row['ticker']
            operation = row['operation']
            amount = row['amount']

            if operation == 'sell':
                invested_amount = ticker_invested_amounts.loc[date, ticker]
                return (amount - invested_amount)
            else:
                return 0

        # Assure-toi que l'index est bien de type datetime
        transactions_df.index = pd.to_datetime(transactions_df.index)

        # Calcul du flux de plus-value
        transactions_df['plus_value_flow'] = transactions_df.apply(calculate_plus_value_flow, axis=1)

        # Agrégation par date
        plus_value_by_date = transactions_df['plus_value_flow'].groupby(transactions_df.index).sum()

        # Création de l'index de dates complet
        full_date_index = pd.date_range(start=self.start_date, end=self.end_date, freq='D')

        # Réindexer avec les dates manquantes
        plus_value_by_date = plus_value_by_date.reindex(full_date_index, fill_value=0)

        # Calcul cumulatif plafonné à 0
        plus_value_cumulative = []
        current_value = 0

        for value in plus_value_by_date:
            current_value += value
            current_value = max(current_value, 0)
            plus_value_cumulative.append(current_value)

        # Résultat final
        result_df = pd.DataFrame({
            'plus_value_flow': plus_value_by_date.values,
            'plus_value_cumulative': plus_value_cumulative
        }, index=full_date_index)

        result_df.index.name = 'index'

        return result_df
    ##########################

    ########## Dividendes ##########
    def calculate_dividends_evolution(self, portfolio_gross_price_evolution: pd.DataFrame, ticker_price_df: pd.DataFrame) -> pd.DataFrame:
        """
        Calcule l'évolution des dividendes pour chaque ticker d'un portefeuille, basée sur les prix bruts et les dividendes distribués,
        en récupérant les dividendes depuis la base de données via les méthodes utilitaires du modèle Dividend.

        Args:
            portfolio_gross_price_evolution (pd.DataFrame): DataFrame contenant l'évolution brute des prix des tickers du portefeuille.
            ticker_price_df (pd.DataFrame): DataFrame contenant les prix des tickers correspondants.

        Returns:
            pd.DataFrame: DataFrame contenant l'évolution des dividendes pour chaque ticker, répartis sur les dates du portefeuille.
        """
        assert isinstance(portfolio_gross_price_evolution, pd.DataFrame), "portfolio_gross_price_evolution doit être un DataFrame"
        assert isinstance(ticker_price_df, pd.DataFrame), "ticker_price_df doit être un DataFrame"

        assert all(isinstance(date, pd.Timestamp) for date in portfolio_gross_price_evolution.index), "L'index de portfolio_gross_price_evolution doit être composé de pd.Timestamp"

        tickers = list(portfolio_gross_price_evolution.columns)

        # Récupérer tous les dividendes en une seule fois sous forme de DataFrame
        raw_dividends_df = Dividend.get_dividends_for_tickers_between_dates(tickers, self.start_date, self.end_date)

        if raw_dividends_df.empty:
            return pd.DataFrame(0, index=portfolio_gross_price_evolution.index, columns=tickers)

        # Initialiser le DataFrame des dividendes avec des zéros
        tickers_dividends = pd.DataFrame(0, index=portfolio_gross_price_evolution.index, columns=tickers, dtype=float)

        for date in raw_dividends_df.index:
            for ticker in raw_dividends_df.columns:
                dividend_amount = raw_dividends_df.at[date, ticker]
                if pd.isna(dividend_amount) or date not in tickers_dividends.index:
                    continue
                try:
                    # Ajuster le dividende en fonction des variations de prix
                    adjusted_dividend = dividend_amount * (
                        portfolio_gross_price_evolution.at[date, ticker] / ticker_price_df.at[date, ticker]
                    )
                    tickers_dividends.at[date, ticker] += adjusted_dividend
                except KeyError:
                    # Cas où la date ou le ticker est manquant dans l’un des DataFrames
                    continue

        return tickers_dividends

    @staticmethod
    def calculate_dividend_earn(transactions: pd.DataFrame) -> float:
        """
        Calcule la somme des dividendes nets encaissés.

        Args:
            transactions (pd.DataFrame): DataFrame avec colonnes 'operation', 'amount', 'fees'.

        Returns:
            float: Montant total des dividendes (net des frais).
        """
        filtres = transactions["operation"] == "dividend"
        return (transactions.loc[filtres, "amount"] - transactions.loc[filtres, "fees"]).sum()
    ################################


    ########## Métriques / Performance ##########
    @staticmethod
    def capital_gain_losses_composed(tickers_invested_amounts: pd.DataFrame, tickers_pru: pd.DataFrame, tickers_prices: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Calcule, pour chaque date et chaque ticker, la valorisation actuelle,
        la performance en pourcentage et la plus-value (ou moins-value) latente
        à partir de l’argent réellement investi.
        """
        
        # Pourcentage
        tickers_gain_pct = (tickers_prices - tickers_pru) / tickers_pru * 100
        # Valorisation
        tickers_valuation = (tickers_invested_amounts * ((tickers_gain_pct / 100) + 1))
        # Plus et moins value l'attente
        tickers_gain = (tickers_valuation - tickers_invested_amounts)

        return tickers_valuation, tickers_gain_pct, tickers_gain
    
    def calculate_pru(self, transaction_df: pd.DataFrame, tickers_invested_amounts: pd.DataFrame) -> pd.DataFrame:
        """
        Calcule le PRU (prix de revient unitaire) jour par jour pour chaque ticker,
        de façon vectorisée, puis masque les jours où l’investissement net est nul.
        """
        # 0) Préparation
        trx_buy = transaction_df[transaction_df["operation"] == "buy"].copy()
        date_range = pd.date_range(self.start_date, self.end_date, freq="D")
        tickers = trx_buy["ticker"].unique()

        # 1) DataFrames cumulés (montant investi & nb d’actions achetées)
        invested = pd.DataFrame(0.0, index=date_range, columns=tickers)
        qty = pd.DataFrame(0.0, index=date_range, columns=tickers)

        # 2) Agrégation achats par (ticker, date)
        for (ticker, date), grp in trx_buy.groupby(["ticker", trx_buy.index]):
            amt = grp["amount"].sum()
            px_u = (grp["amount"] * grp["stock_price"]).sum() / amt
            invested.at[date, ticker] += amt
            qty.at[date, ticker] += amt / px_u

        # 3) Cumuls et PRU vectorisés
        invested_cum = invested.cumsum()
        qty_cum = qty.cumsum()
        pru = invested_cum / qty_cum
        pru.ffill(inplace=True) # propage tant qu'une position existe

        # 4) Masque : quand l’investissement net est retombé à 0, on met NaN
        pru = pru.reindex_like(tickers_invested_amounts)   # même shape/ordre
        pru[tickers_invested_amounts == 0] = None          # ⬅️ masque exact d'origine

        return pru
    
    def calculate_portfolio_cagr(self, portfolio_valuation: pd.Series, horizons_years=(1, 2, 3, 5, 10)):
        """
        Calcule le CAGR du portefeuille sur plusieurs horizons.
        
        Args:
            portfolio_valuation (pd.Series): index datetime, valeurs = valorisation portefeuille.
            horizons_years (Iterable[int]): horizons en années.
        
        Returns:
            dict[horizon, float]: CAGR par horizon (NaN si période indisponible).
        """
        # 1) Sélection de la date de fin : on enlève l'heure et on s'assure qu'elle existe dans l'index
        today = pd.Timestamp(self.end_date).normalize()
        if today not in portfolio_valuation.index:
            possible_ends = portfolio_valuation.index[portfolio_valuation.index <= today]
            if possible_ends.empty:
                raise ValueError("Aucune date ≤ end_date dans la série.")
            today = possible_ends.max()

        # 2) (Optionnel) On peut retirer les zéros initiaux
        portfolio_valuation = portfolio_valuation.loc[portfolio_valuation.ne(0).idxmax():]
        
        end_val = portfolio_valuation.loc[today]

        cagr_results = {}
        for horizon in horizons_years:
            start_target = today - pd.DateOffset(years=horizon)

            # date de départ : dernière date ≤ start_target
            possible_starts = portfolio_valuation.index[portfolio_valuation.index <= start_target]
            if possible_starts.empty:
                cagr_results[horizon] = None
                continue
            start_date = possible_starts.max()

            start_val = portfolio_valuation.loc[start_date]

            if pd.isna(start_val) or start_val == 0 or pd.isna(end_val):
                cagr_results[horizon] = None
                continue

            cagr = (end_val / start_val) ** (1 / horizon) - 1
            cagr_results[horizon] = round(float(cagr * 100), 2)

        # 4) CAGR depuis l'origine (« all »)
        first_date = portfolio_valuation.index[0]
        first_val = portfolio_valuation.iloc[0]

        if first_date < today and first_val not in (0, None):
            n_years_total = (today - first_date).days / 365.25
            if n_years_total > 0:
                total_cagr = (end_val / first_val) ** (1 / n_years_total) - 1
                cagr_results["all"] = round(float(total_cagr * 100), 2)
            else:
                cagr_results["all"] = None
        else:
            cagr_results["all"] = None

        return cagr_results
    
    @staticmethod
    def calculate_portfolio_sharpe_ratio(portfolio_valuation: pd.DataFrame, risk_free_rate_annual: float = 0.025, periods: str='annuel') -> pd.Series:
        """
        Calcule le ratio de Sharpe annualisé du portefeuille.

        Args:
            portfolio_valuation (pd.Series):
                Index datetime, valeurs = valorisation totale du portefeuille.
            risk_free_rate_annual (float, optional):
                Taux sans risque annuel (ex.: 0.02 pour 2 %).
            periods (str, optional):
                La fréquence doit être 'journalier', 'mensuel' ou 'annuel'.

        Returns:
            float: Sharpe ratio annualisé (np.nan si impossible à calculer).

        Explication:
            Le **ratio de Sharpe** est une mesure qui permet d'évaluer la rentabilité ajustée au risque d'un portefeuille d'investissement.
            Il est calculé en prenant la différence entre le rendement moyen du portefeuille et le rendement sans risque,
            puis en la divisant par la volatilité (écart-type) des rendements du portefeuille. 
            Plus le ratio de Sharpe est élevé, plus le portefeuille offre un bon rendement par rapport à son risque.

            Le ratio de Sharpe est particulièrement utile pour comparer différents portefeuilles ou stratégies d'investissement,
            car il permet de déterminer lequel génère le plus de rendement par unité de risque.

            Si le ratio est compris entre 0 et 1, le sur-rendement du portefeuille considéré par rapport au référentiel se fait pour une prise de risque trop élevée.
            Ou, le risque pris est trop élevé pour le rendement obtenu.

            Si le ratio est supérieur à 1, le rendement du portefeuille dépasse la performance du référentiel pour une prise de risque ad hoc.
            Autrement dit, la sur-performance ne se fait pas au prix d'un risque trop élevé.
        """
        assert periods in ['journalier', 'mensuel', 'annuel'], "La fréquence doit être 'journalier', 'mensuel' ou 'annuel'."

        portfolio_valuation = portfolio_valuation.loc[portfolio_valuation.ne(0).idxmax():]
        # Calcul des rendements en fonction de la fréquence choisie
        if periods == 'journalier':
            rendements = portfolio_valuation.pct_change().dropna()
        elif periods == 'mensuel':
            rendements = portfolio_valuation.resample('ME').ffill().pct_change().dropna()
        elif periods == 'annuel':
            rendements = portfolio_valuation.resample('YE').ffill().pct_change().dropna()

        # Calcul du rendement moyen et de la volatilité
        rendementsMoyens = rendements.mean() * (252 if periods == 'journalier' else (12 if periods == 'mensuel' else 1))
        volatilité = rendements.std() * (252 ** 0.5 if periods == 'journalier' else (12 ** 0.5 if periods == 'mensuel' else 1))

        # Calcul du ratio de Sharpe
        ratioSharpe = (rendementsMoyens - risk_free_rate_annual) / volatilité

        # Retourne un DataFrame avec une colonne "ratioSharpe"
        return round(ratioSharpe, 2)
    
    @staticmethod
    def calculate_portfolio_sortino_ratio(portfolio_valuation: pd.Series, risk_free_rate_annual: float = 0.025, periods_per_year: int = 252) -> float:
        """
        Calcule le ratio de Sortino annualisé du portefeuille.

        Args:
            portfolio_valuation (pd.Series): index datetime, valeurs = valorisation portefeuille.
            risk_free_rate_annual (float): taux sans risque annuel (ex: 0.02 pour 2%).
            periods_per_year (int): nombre de périodes par an (252 pour jours de bourse).

        Returns:
            float: ratio de Sortino annualisé (np.nan si calcul impossible).

        Explication:
            Le **ratio de Sortino** est une version améliorée du ratio de Sharpe qui ne prend en compte que la volatilité des rendements négatifs,
            plutôt que la volatilité totale des rendements.
            L'objectif est de mesurer la performance ajustée en fonction du risque, mais en ne considérant que
            les rendements qui sont inférieurs à un certain seuil (souvent fixé à 0, ce qui signifie les rendements négatifs).
            Cela permet de mieux évaluer un portefeuille en se concentrant uniquement sur les périodes où il y a des pertes,
            plutôt que d'inclure aussi les périodes de rendements positifs.

            Un ratio de Sortino plus élevé indique une meilleure performance ajustée au risque de perte.
            Un ratio élevé signifie qu'un portefeuille génère un rendement élevé par rapport aux risques de pertes qu'il comporte.

            En dessous de 1 : le ratio de Sortino est mauvais / médiocre — ça signifie que le portefeuille ne compense pas assez les risques à la baisse par rapport au rendement.
            Entre 1 et 2 : c’est bon — le portefeuille offre un bon compromis rendement/risque baissier.
            Au-dessus de 2 : c’est très bon — le portefeuille performe vraiment bien en limitant bien les pertes par rapport au gain.
        """
        # On retire les premiers zéros pour éviter les distorsions
        portfolio_valuation = portfolio_valuation.loc[portfolio_valuation.ne(0).idxmax():]

        # Calcul des rendements périodiques
        returns = portfolio_valuation.pct_change().dropna()
        if returns.empty:
            return np.nan

        # Taux sans risque périodique
        risk_free_rate_periodic = (1 + risk_free_rate_annual) ** (1 / periods_per_year) - 1

        # Rendements excédentaires
        excess_returns = returns - risk_free_rate_periodic

        # Calcul de la volatilité des rendements négatifs (downside deviation)
        negative_returns = excess_returns[excess_returns < 0]
        if negative_returns.empty:
            return np.nan  # Pas de pertes, Sortino pas défini

        downside_deviation = np.sqrt(np.mean(negative_returns ** 2))

        if downside_deviation == 0 or pd.isna(downside_deviation):
            return np.nan

        # Moyenne des rendements excédentaires
        mean_excess_return = excess_returns.mean()

        # Ratio de Sortino annualisé
        sortino_ratio = mean_excess_return / downside_deviation * np.sqrt(periods_per_year)

        return round(float(sortino_ratio), 2)
    
    @staticmethod
    def calculate_ecart_type(portfolio_valuation: pd.Series) -> pd.Series:
        """
        Calcule l'écart-type des rendements quotidiens pour chaque portefeuille dans un DataFrame.
    
        Explication:
            L'écart-type est une mesure statistique qui quantifie la dispersion des rendements par rapport à la moyenne. 
            Un écart-type élevé indique que les rendements sont très dispersés autour de la moyenne,
            tandis qu'un écart-type faible signifie que les rendements sont plus concentrés autour de la moyenne.

            L'écart-type des rendements est un indicateur clé de la volatilité d'un portefeuille.
            Un portefeuille avec un écart-type élevé a des rendements plus variables et donc plus risqués.

        Args:
            portfolio_valuation (pd.Series): Une Serie avec pour index des dates.

        Returns:
            pd.Series: Une série contenant l'écart-type des rendements pour chaque portefeuille.
        """
        assert not portfolio_valuation.empty, "Le DataFrame ne doit pas être vide."
        portfolio_valuation = portfolio_valuation.loc[portfolio_valuation.ne(0).idxmax():]
        
        # Calcul des rendements quotidiens
        rendements = portfolio_valuation.pct_change().dropna()
        # Calcul de l'écart-type des rendements
        ecart_type = rendements.std() * 100  # On multiplie par 100 pour avoir en pourcentage

        return round(ecart_type, 2)
    
    @staticmethod
    def calculer_drawdown_max(portfolio_valuation: pd.Series) -> dict:
        """
        Calcule le drawdown maximal d'une série représentant la valorisation d'un portefeuille.

        Explication:
            Un **drawdown** représente la baisse maximale d'un actif ou d'un portefeuille par rapport à son sommet historique.
            Cela mesure la perte de valeur par rapport au point le plus élevé atteint avant que la valeur ne chute.
            Un drawdown est exprimé en pourcentage et il est généralement utilisé pour évaluer le risque d'un portefeuille.
            Plus le drawdown est important, plus la perte potentielle est élevée, ce qui signifie un risque plus grand pour l'investisseur.

            Le **drawdown maximal** est le plus grand drawdown observé pendant la période de l'investissement.
            La plage de dates associée correspond à la période entre le point où le prix a atteint son maximum historique et la date à laquelle le drawdown maximal a été observé.

        Args:
            portfolio_valuation (pd.Series): série pandas avec un index datetime et les valeurs de valorisation du portefeuille.

        Returns:
            dict: contenant :
                - 'drawdown_max' (float): drawdown maximal en pourcentage négatif,
                - 'date_max_before_drawdown' (date): date du sommet historique avant le drawdown maximal,
                - 'date_drawdown_max' (date): date du drawdown maximal.
        """

        portfolio_valuation = portfolio_valuation.loc[portfolio_valuation.ne(0).idxmax():]
        # Validation minimale
        if portfolio_valuation.empty:
            raise ValueError("La série 'portfolio_valuation' est vide.")
        
        # Nettoyage éventuel
        portfolio_valuation = portfolio_valuation.dropna()

        # Plus-haut historique à chaque date
        rolling_peak = portfolio_valuation.cummax()

        # Drawdown instantané (exprimé sur 100 ➔ pour-cent)
        drawdowns = (portfolio_valuation / rolling_peak - 1.0) * 100

        # Drawdown maximal (le plus négatif)
        drawdown_max = float(drawdowns.min())
        date_drawdown_max = drawdowns.idxmin()

        # Date du dernier sommet avant le drawdown maximal
        peak_value_at_dd = rolling_peak.loc[date_drawdown_max]
        peak_slice = portfolio_valuation.loc[:date_drawdown_max]
        date_max_before_drawdown = peak_slice[peak_slice == peak_value_at_dd].index[-1]

        return {
            "drawdown_max": round(drawdown_max, 2),
            "date_max_before_drawdown": date_max_before_drawdown.date(),
            "date_drawdown_max": date_drawdown_max.date(),
        }

    @staticmethod
    def calculer_drawdown_max_un_jour(portfolio_valuation: pd.Series) -> list:
        """
        Calcule le drawdown maximal sur une seule journée pour une série de valorisation de portefeuille.
        Le drawdown maximal est la plus grande perte quotidienne observée (par rapport au jour précédent).

        Args:
            portfolio_valuation (pd.Series): Série avec index datetime et valeurs de valorisation.

        Returns:
            list: [drawdown_max en %, date du drawdown] ou [np.nan, None] si données insuffisantes.
        """
        assert isinstance(portfolio_valuation, pd.Series), "Le paramètre doit être une pd.Series."
        assert not portfolio_valuation.empty, "La série ne doit pas être vide."
        assert isinstance(portfolio_valuation.index, pd.DatetimeIndex), "L'index doit être un DatetimeIndex."

        portfolio_valuation = portfolio_valuation.loc[portfolio_valuation.ne(0).idxmax():]
        rendements = portfolio_valuation.pct_change().dropna()

        if rendements.empty:
            return [np.nan, None]

        drawdown_max = rendements.min()
        date_drawdown_max = rendements.idxmin()

        return [round(float(drawdown_max * 100), 2), date_drawdown_max]
    
    @staticmethod
    def calculate_dividend_yield(transaction_df: pd.Series, portfolio_valuation: pd.Series) -> float:
        """
        Calcule le rendement du dividende en pourcentage.
        """
        total_dividendes = (transaction_df.loc[transaction_df["operation"] == "dividend", "amount"]
                    - transaction_df.loc[transaction_df["operation"] == "dividend", "fees"]).sum()
        
        return round((total_dividendes / portfolio_valuation.iloc[-1]) * 100, 2)
    #############################################
