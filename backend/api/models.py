from collections import defaultdict
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Type
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from django.conf import settings
from django.db.models import Sum
import pandas as pd
from django.db.models import Min, Max
from django.core.exceptions import ObjectDoesNotExist

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email obligatoire")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email

class UserPreference(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return f"Préférences de {self.user.email}"


CURRENCY_CHOICES = [
    ('USD', '$'),
    ('EUR', '€'),
]

PORTFOLIO_MAIN_NAME = "all"

class Company(models.Model):
    name = models.CharField(max_length=20)
    ticker = models.CharField(max_length=5, unique=True, primary_key=True)
    isin = models.CharField(max_length=12, unique=True, blank=True, null=True)
    sector = models.CharField(max_length=50, blank=True, null=True)
    country = models.CharField(max_length=50, blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    founded_date = models.DateField(blank=True, null=True)
    stock_exchange = models.CharField(max_length=50, blank=True, null=True)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES)

    class Meta:
        verbose_name = "Entreprise"
        verbose_name_plural = "Entreprises"

    def __str__(self):
        return self.ticker

class StockPrice(models.Model):
    ticker = models.ForeignKey(Company, on_delete=models.CASCADE, to_field="ticker", db_column="ticker")
    date = models.DateField(blank=False, null=False)
    open_price = models.DecimalField(max_digits=12, decimal_places=6)
    high_price = models.DecimalField(max_digits=12, decimal_places=6)
    low_price = models.DecimalField(max_digits=12, decimal_places=6)
    close_price = models.DecimalField(max_digits=12, decimal_places=6)
    volume = models.BigIntegerField()

    class Meta:
        unique_together = ("ticker", "date")
        indexes = [
            models.Index(fields=["ticker"]),
            models.Index(fields=["date"]),
        ]

    def __str__(self):
        return f"{self.ticker} - {self.date}"

    @classmethod
    def get_open_prices_dataframe_for_all_users(cls) -> pd.DataFrame:
        """
        Retourne un DataFrame avec les open_price pour tous les tickers
        présents dans tous les portefeuilles, indexé par date.
        """
        # Étape 1 : tous les tickers uniques utilisés dans les portefeuilles
        tickers = (
            PortfolioTicker.objects
            .values_list('ticker__ticker', flat=True)
            .distinct()
        )

        # Étape 2 : récupération des données de prix
        prices = cls.objects.filter(ticker_id__in=tickers)

        if not prices.exists():
            return pd.DataFrame()

        # Étape 3 : transformation en DataFrame
        df = pd.DataFrame.from_records(
            prices.values('date', 'ticker_id', 'open_price')
        )

        # Étape 4 : pivot pour format souhaité
        df_pivot = df.pivot(index='date', columns='ticker_id', values='open_price')
        df_pivot.sort_index(inplace=True)
    
        # Conversion en float pour éviter les problèmes Decimal
        df_pivot = df_pivot.astype(float)

        return df_pivot

    @classmethod
    def get_open_prices_dataframe_for_user(cls, user: CustomUser) -> pd.DataFrame:
        """
        Retourne un DataFrame avec les open_price pour tous les tickers
        détenus par un utilisateur, indexé par date.
        """
        # Étape 1 : récupérer les tickers uniques de l'utilisateur
        tickers = (
            PortfolioTicker.objects
            .filter(portfolio__user=user)
            .values_list('ticker__ticker', flat=True)
            .distinct()
        )

        # Étape 2 : récupérer les données StockPrice correspondantes
        prices = cls.objects.filter(ticker_id__in=tickers)

        if not prices.exists():
            return pd.DataFrame()  # aucun prix trouvé

        # Étape 3 : construire un DataFrame
        df = pd.DataFrame.from_records(
            prices.values('date', 'ticker_id', 'open_price')
        )

        # Étape 4 : pivot pour mettre les tickers en colonnes
        df_pivot = df.pivot(index='date', columns='ticker_id', values='open_price')
        df_pivot.sort_index(inplace=True)

        # Forcer l'index en pd.Timestamp
        df_pivot.index = pd.to_datetime(df_pivot.index)
    
        # Conversion en float pour éviter les problèmes Decimal
        df_pivot = df_pivot.astype(float)

        return df_pivot

    @classmethod
    def get_open_prices_dataframe_for_user_start_date(
        cls,
        user: CustomUser,
        start_date: datetime
    ) -> pd.DataFrame:
        """
        Retourne un DataFrame avec les open_price pour tous les tickers
        détenus par un utilisateur, indexé par date, à partir de start_date.
        """
        # Étape 1 : récupérer les tickers uniques de l'utilisateur
        tickers = (
            PortfolioTicker.objects
            .filter(portfolio__user=user)
            .values_list('ticker__ticker', flat=True)
            .distinct()
        )

        # Étape 2 : récupérer les données StockPrice correspondantes à partir de start_date
        prices = cls.objects.filter(
            ticker_id__in=tickers,
            date__gte=(start_date - timedelta(days=3))
        )

        if not prices.exists():
            return pd.DataFrame()  # aucun prix trouvé

        # Étape 3 : construire un DataFrame
        df = pd.DataFrame.from_records(
            prices.values('date', 'ticker_id', 'open_price')
        )

        # Étape 4 : pivot pour mettre les tickers en colonnes
        df_pivot = df.pivot(index='date', columns='ticker_id', values='open_price')
        df_pivot.sort_index(inplace=True)

        # Conversion en float pour éviter les problèmes Decimal
        df_pivot = df_pivot.astype(float)

        return df_pivot

    @classmethod
    def get_open_prices_dataframe_for_tickers(cls, tickers: list[str]) -> pd.DataFrame:
        """
        Retourne un DataFrame avec les open_price pour les tickers passés en paramètre,
        indexé par date.
        
        :param tickers: liste des tickers à récupérer
        :return: DataFrame avec index date et colonnes tickers
        """
        if not tickers:
            return pd.DataFrame()

        # Filtrer les prix pour les tickers donnés
        prices = cls.objects.filter(ticker_id__in=tickers)

        if not prices.exists():
            return pd.DataFrame()

        # Transformer en DataFrame
        df = pd.DataFrame.from_records(
            prices.values('date', 'ticker', 'open_price')
        )

        # Pivot pour format souhaité
        df_pivot = df.pivot(index='date', columns='ticker', values='open_price')
        df_pivot.sort_index(inplace=True)
        df_pivot.index = pd.to_datetime(df_pivot.index)
    
        # Conversion en float pour éviter les problèmes Decimal
        df_pivot = df_pivot.astype(float)

        return df_pivot

    @classmethod
    def get_open_prices_dataframe_for_ticker(cls, ticker: str) -> pd.DataFrame:
        """
        Retourne un DataFrame avec les open_price pour le ticker passé en paramètre,
        indexé par date.
        
        :param ticker: ticker à récupérer
        :return: DataFrame avec index date et une colonne = ticker
        """
        if not ticker:
            return pd.DataFrame()

        # Filtrer les prix pour le ticker donné
        prices = cls.objects.filter(ticker_id=ticker)

        if not prices.exists():
            return pd.DataFrame()

        # Transformer en DataFrame
        df = pd.DataFrame.from_records(
            prices.values('date', 'ticker', 'open_price')
        )

        # Pivot pour avoir une colonne avec le ticker
        df_pivot = df.pivot(index='date', columns='ticker', values='open_price')
        df_pivot.sort_index(inplace=True)
        df_pivot.index = pd.to_datetime(df_pivot.index)

        # Conversion en float
        df_pivot = df_pivot.astype(float)

        return df_pivot

    @classmethod
    def convert_dataframe_to_currency(cls, df: pd.DataFrame, target_currency: str) -> pd.DataFrame:
        """
        Convertit les colonnes (tickers) d'un DataFrame vers la devise cible (USD ou EUR).

        :param df: DataFrame avec colonnes = tickers, index = dates
        :param target_currency: "USD" ou "EUR"
        :return: DataFrame converti
        """
        if df.empty:
            return df

        if target_currency not in ["USD", "EUR"]:
            raise ValueError("La devise cible doit être USD ou EUR")

        # Récupérer les devises de chaque ticker
        tickers_currencies = dict(
            Company.objects.filter(ticker__in=df.columns)
            .values_list("ticker", "currency")
        )

        # Récupérer le taux de change EUR/USD depuis StockPrice
        fx_ticker = "EURUSD=X"
        fx_prices = (
            cls.objects.filter(ticker_id=fx_ticker, date__in=df.index)
            .values("date", "open_price")
        )
        if not fx_prices.exists():
            raise ValueError("Pas de données de change disponibles pour EURUSD=X")

        fx_df = pd.DataFrame.from_records(fx_prices)
        fx_df.set_index("date", inplace=True)
        fx_df.sort_index(inplace=True)
        fx_df = fx_df.astype(float)

        # Assurer qu’on aligne les dates du FX avec df
        fx_df = fx_df.reindex(df.index).ffill().bfill()

        # Conversion colonne par colonne
        converted_df = df.copy()
        for ticker in df.columns:
            ticker_currency = tickers_currencies.get(ticker)

            if ticker_currency is None:
                continue  # sécurité : ticker absent de Company

            if ticker_currency == target_currency:
                continue  # rien à faire

            if ticker_currency == "USD" and target_currency == "EUR":
                # USD → EUR : diviser par le taux EURUSD
                converted_df[ticker] = df[ticker] / fx_df["open_price"]

            elif ticker_currency == "EUR" and target_currency == "USD":
                # EUR → USD : multiplier par le taux EURUSD
                converted_df[ticker] = df[ticker] * fx_df["open_price"]

        return converted_df

    @classmethod
    def get_price_on_date(cls, ticker: str, date: datetime, target_currency: str) -> float:
        """
        Retourne le prix d'ouverture d'un ticker donné à une date précise (ou la dernière date dispo avant),
        converti dans la devise cible (USD ou EUR).
        """

        if target_currency not in ["USD", "EUR"]:
            raise ValueError("La devise cible doit être USD ou EUR")

        # Récupération du dernier prix <= date
        stock = (
            cls.objects.filter(ticker_id=ticker, date__lte=date)
            .order_by("-date")
            .first()
        )
        if not stock:
            raise ValueError(f"Pas de prix disponible pour {ticker} avant ou à la date {date}")

        price = float(stock.open_price)

        # Récupération de la devise du ticker
        try:
            ticker_currency = Company.objects.get(ticker=ticker).currency
        except ObjectDoesNotExist:
            raise ValueError(f"Ticker {ticker} introuvable dans Company")

        return StockPrice.convert_price(price, ticker_currency, target_currency, date)
    
    @classmethod
    def convert_price(cls, price: float, from_currency: str, to_currency: str, date: datetime) -> float:
        """
        Convertit un prix d'une devise vers une autre à une date donnée.

        :param price: montant à convertir
        :param from_currency: devise d'origine ("USD" ou "EUR")
        :param to_currency: devise cible ("USD" ou "EUR")
        :param date: date de référence pour le taux de change
        :return: prix converti
        """
        if from_currency == to_currency:
            return price

        fx_ticker = "EURUSD=X"

        # Récupérer le taux de change le plus proche (<= date)
        fx_obj = (
            cls.objects.filter(ticker_id=fx_ticker, date__lte=date)
            .order_by("-date")
            .first()
        )
        if not fx_obj:
            raise ValueError(f"Aucun taux de change trouvé pour {fx_ticker} avant {date}")

        fx_rate = float(fx_obj.open_price)

        if from_currency == "USD" and to_currency == "EUR":
            return price / fx_rate
        elif from_currency == "EUR" and to_currency == "USD":
            return price * fx_rate

        raise ValueError(f"Conversion non supportée : {from_currency} → {to_currency}")


class StockSplit(models.Model):
    ticker = models.ForeignKey(Company, on_delete=models.CASCADE, to_field='ticker', db_column='ticker')
    date = models.DateField()
    ratio = models.FloatField()  # Exemple : 2.0 pour un split 2:1

    class Meta:
        unique_together = ("ticker", "date")
        indexes = [
            models.Index(fields=["ticker", "date"]),
        ]

    def __str__(self):
        return f"{self.ticker.ticker} - {self.date} : {self.ratio}"

    @staticmethod
    def get_splits_from_db(tickers: list[str]) -> dict:
        """
        Récupère les splits depuis la base de données pour une liste de tickers.

        Args:
            tickers (List[str]): Liste des tickers (symboles).

        Returns:
            dict: Un dictionnaire avec les tickers en clés et un pd.Series (index=date, valeur=ratio) en valeurs.
        """
        from django.db.models import F

        splits = (
            StockSplit.objects
            .filter(ticker__ticker__in=tickers)
            .values_list("ticker__ticker", "date", "ratio")
            .order_by("ticker__ticker", "date")
        )

        result = defaultdict(list)
        for ticker, date, ratio in splits:
            result[ticker].append((pd.to_datetime(date), ratio))

        # Conversion en Series pour faciliter la manipulation avec pandas
        splits_dict = {
            ticker: pd.Series(
                data=[ratio for date, ratio in values],
                index=[date for date, ratio in values]
            )
            for ticker, values in result.items()
        }

        return splits_dict

    @classmethod
    def apply_splits(cls, transactions_df: pd.DataFrame) -> pd.DataFrame:
        """
        Ajuste les colonnes 'quantity' et 'stock_price' en fonction des splits stockés en base de données.
        """
        if transactions_df.empty:
            return transactions_df

        # Vérifie colonnes
        required_cols = {"ticker", "quantity", "stock_price"}
        if not required_cols.issubset(transactions_df.columns):
            raise ValueError(f"Le DataFrame doit contenir les colonnes {required_cols}")

        # Récupération des splits depuis la base
        tickers = transactions_df["ticker"].dropna().unique().tolist()
        splits_dict = cls.get_splits_from_db(tickers)

        def ajuster_ligne(row):
            ticker = row["ticker"]
            date_transaction = pd.to_datetime(row.name)  # Index = datetime
            quantite = row["quantity"]
            prix = row["stock_price"]

            if ticker not in splits_dict:
                return pd.Series({"quantity": quantite, "stock_price": prix})

            splits = splits_dict[ticker]

            # Splits après la date de transaction
            splits_apres = splits[splits.index > date_transaction]
            facteur_split = splits_apres.prod() if not splits_apres.empty else 1.0

            return pd.Series({
                "quantity": quantite * facteur_split,
                "stock_price": prix / facteur_split
            })

        ajustements = transactions_df.apply(
            lambda row: ajuster_ligne(row) if pd.notna(row["ticker"]) else pd.Series({
                "quantity": row["quantity"],
                "stock_price": row["stock_price"]
            }),
            axis=1
        )

        transactions_df["quantity"] = ajustements["quantity"]
        transactions_df["stock_price"] = ajustements["stock_price"]

        return transactions_df

class Dividend(models.Model):
    ticker = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        to_field="ticker",
        db_column="ticker"
    )
    date = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        unique_together = ("ticker", "date")
        indexes = [
            models.Index(fields=["ticker", "date"]),
        ]
        verbose_name = "Dividende"
        verbose_name_plural = "Dividendes"

    def __str__(self):
        return f"{self.ticker.ticker} - {self.date} : {self.amount}"

    @classmethod
    def get_dividends_for_ticker(cls, ticker: str) -> pd.DataFrame:
        dividends = cls.objects.filter(ticker__ticker=ticker)

        if not dividends.exists():
            return pd.DataFrame()

        df = pd.DataFrame.from_records(
            dividends.values("date", "amount")
        )
        df.set_index("date", inplace=True)
        df.index = pd.to_datetime(df.index)
        df.sort_index(inplace=True)
        df = df.astype(float)

        return df.rename(columns={"amount": ticker})

    @classmethod
    def get_dividends_for_tickers(cls, tickers: list[str]) -> pd.DataFrame:
        if not tickers:
            return pd.DataFrame()

        dividends = cls.objects.filter(ticker__ticker__in=tickers)

        if not dividends.exists():
            return pd.DataFrame()

        df = pd.DataFrame.from_records(
            dividends.values("date", "ticker__ticker", "amount"),
            columns=["date", "ticker", "amount"]
        )

        df_pivot = df.pivot(index="date", columns="ticker", values="amount")
        df_pivot.index = pd.to_datetime(df_pivot.index)
        df_pivot.sort_index(inplace=True)
        df_pivot = df_pivot.astype(float)

        return df_pivot

    @classmethod
    def get_dividends_for_tickers_between_dates(
        cls,
        tickers: list[str],
        start_date: datetime,
        end_date: datetime
    ) -> pd.DataFrame:
        """
        Retourne un DataFrame des dividendes pour plusieurs tickers, filtrés entre start_date et end_date inclus.
        """
        if not tickers:
            return pd.DataFrame()

        dividends = cls.objects.filter(
            ticker__ticker__in=tickers,
            date__gte=start_date,
            date__lte=end_date
        )

        if not dividends.exists():
            return pd.DataFrame()

        # ⚠️ Ne pas passer `columns=[...]` → sinon pandas croit que tu imposes l’ordre
        df = pd.DataFrame.from_records(dividends.values("date", "ticker__ticker", "amount"))

        # Renommer correctement la colonne du ticker
        df.rename(columns={"ticker__ticker": "ticker"}, inplace=True)

        # Pivot → colonnes = tickers
        df_pivot = df.pivot(index="date", columns="ticker", values="amount")

        df_pivot.index = pd.to_datetime(df_pivot.index)
        df_pivot.sort_index(inplace=True)
        df_pivot = df_pivot.astype(float)

        return df_pivot

class Portfolio(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.user.email} - {self.name}"

    @classmethod
    def get_user_portfolios(cls: Type['Portfolio'], user):
        return cls.objects.filter(user=user)

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)

        if is_new:
            # Crée PORTFOLIO_MAIN_NAME s’il n’existe pas encore pour cet utilisateur
            Portfolio.objects.get_or_create(user=self.user, name=PORTFOLIO_MAIN_NAME)

    @classmethod
    def get_user_portfolio_name(cls, user_id: int, portfolio_id: int) -> str | None:
        """
        Retourne le nom d'un portefeuille pour un utilisateur donné à partir de leurs IDs.
        """
        try:
            portfolio = cls.objects.get(pk=portfolio_id, user_id=user_id)
            return portfolio.name
        except cls.DoesNotExist:
            return None

class PortfolioTicker(models.Model):
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE)
    ticker = models.ForeignKey(Company, on_delete=models.CASCADE, to_field='ticker', db_column='ticker')
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES)

    class Meta:
        unique_together = ("portfolio", "ticker", "currency")

    def __str__(self):
        return f"{self.portfolio.name} - {self.ticker} - {self.currency}"

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)

        if is_new and self.portfolio.name != PORTFOLIO_MAIN_NAME:
            # Ajouter dans PORTFOLIO_MAIN_NAME si ticker/currency manquant
            global_portfolio, _ = Portfolio.objects.get_or_create(user=self.portfolio.user, name=PORTFOLIO_MAIN_NAME)
            PortfolioTicker.objects.get_or_create(
                portfolio=global_portfolio,
                ticker=self.ticker,
                currency=self.currency
            )

    def delete(self, *args, **kwargs):
        user = self.portfolio.user

        # Supprimer seulement si ce n'est pas PORTFOLIO_MAIN_NAME
        if self.portfolio.name != PORTFOLIO_MAIN_NAME:
            global_portfolio = Portfolio.objects.get(user=user, name=PORTFOLIO_MAIN_NAME)

            # Le ticker dans le portefeuille global
            global_ticker = PortfolioTicker.objects.filter(
                portfolio=global_portfolio,
                ticker=self.ticker,
                currency=self.currency
            ).first()

            if global_ticker:
                # Est-ce qu’il reste un autre portefeuille (hors PORTFOLIO_MAIN_NAME) qui utilise ce ticker/currency ?
                other_portfolios = Portfolio.objects.filter(user=user).exclude(name=PORTFOLIO_MAIN_NAME)
                ticker_still_used = PortfolioTicker.objects.filter(
                    portfolio__in=other_portfolios,
                    ticker=self.ticker,
                    currency=self.currency
                ).exclude(pk=self.pk).exists()

                if not ticker_still_used:
                    # Est-ce qu'il reste des transactions associées dans PORTFOLIO_MAIN_NAME ?
                    has_transactions = PortfolioTransaction.objects.filter(
                        portfolio=global_portfolio,
                        portfolio_ticker=global_ticker
                    ).exists()

                    if not has_transactions:
                        global_ticker.delete()

        super().delete(*args, **kwargs)

    @classmethod
    def get_all_unique_tickers(cls) -> list:
        """
        Retourne une liste unique des tickers (code) pour TOUS les utilisateurs,
        en supprimant les doublons sur (ticker, currency).
        """
        tickers = (
            cls.objects
            .values_list('ticker__ticker', 'currency')
            .distinct()
        )
        # On retourne juste les tickers uniques
        return list({ticker for ticker, _ in tickers})

    @classmethod
    def get_user_unique_tickers(cls, user) -> list:
        """
        Retourne une liste unique des tickers (code) pour un utilisateur,
        en supprimant les doublons sur (ticker, currency).
        """
        tickers = (
            cls.objects
            .filter(portfolio__user=user)
            .values_list('ticker__ticker', 'currency')
            .distinct()
        )
        # On retourne la liste des tickers (tu peux adapter selon ton besoin)
        return list({ticker for ticker, _ in tickers})

    @classmethod
    def get_user_tickers_by_currency(cls, user_id: int, portfolio_id: int) -> dict[str, list[str]]:
        """
        Retourne les tickers de l'utilisateur groupés par devise
        pour un portefeuille spécifique.
        
        :param user_id: ID de l'utilisateur
        :param portfolio_id: ID du portefeuille
        :return: dict avec devise comme clé et liste de tickers comme valeur
        """
        tickers = (
            cls.objects
            .filter(
                portfolio__user_id=user_id,
                portfolio_id=portfolio_id
            )
            .values("ticker__ticker", "currency")
            .distinct()
        )

        result: dict[str, list[str]] = {}
        for t in tickers:
            currency = t["currency"]
            ticker = t["ticker__ticker"]
            result.setdefault(currency, []).append(ticker)

        return result

    @classmethod
    def get_currencies_for_ticker(cls, user_id: int, portfolio_id: int, ticker: str) -> list[str]:
        """
        Retourne la liste unique des devises associées à un ticker
        pour un utilisateur donné et un portefeuille précis.

        :param user_id: id de l'utilisateur
        :param portfolio_id: id du portefeuille
        :param ticker: code du ticker (ex: "AAPL")
        :return: liste des devises (ex: ["USD", "EUR"])
        """
        currencies = (
            cls.objects
            .filter(
                portfolio__user_id=user_id,
                portfolio_id=portfolio_id,
                ticker__ticker=ticker
            )
            .values_list("currency", flat=True)
            .distinct()
        )
        return sorted(list(currencies))

class PortfolioTransaction(models.Model):
    OPERATION_CHOICES = [
        ('buy', 'Achat'),
        ('sell', 'Vente'),
        ('dividend', 'Dividende'),
        ('interest', 'Intérêt'),
        ('deposit', "Dépôt"),
        ('withdrawal', "Retrait"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE)
    portfolio_ticker = models.ForeignKey(PortfolioTicker, on_delete=models.CASCADE, blank=True, null=True)
    operation = models.CharField(max_length=10, choices=OPERATION_CHOICES)
    date = models.DateField(blank=False, null=False)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    fees = models.DecimalField(max_digits=12, decimal_places=2)
    stock_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, blank=True, null=True)

    def __str__(self):
        return f"{self.operation.upper()} - {self.portfolio_ticker.ticker if self.portfolio_ticker else 'N/A'} - {self.quantity}"
    
    @classmethod
    def total_fees_for_portfolio(cls, portfolio):
        return cls.objects.filter(portfolio=portfolio).aggregate(total_fees=Sum('fees'))['total_fees'] or 0

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        old_tx = None

        if not is_new and self.pk:
            try:
                old_tx = PortfolioTransaction.objects.get(pk=self.pk)
            except PortfolioTransaction.DoesNotExist:
                old_tx = None

        super().save(*args, **kwargs)

        if self.portfolio.name == PORTFOLIO_MAIN_NAME:
            return

        global_portfolio, _ = Portfolio.objects.get_or_create(user=self.user, name=PORTFOLIO_MAIN_NAME)

        global_ticker = None
        if self.portfolio_ticker:
            global_ticker, _ = PortfolioTicker.objects.get_or_create(
                portfolio=global_portfolio,
                ticker=self.portfolio_ticker.ticker,
                currency=self.portfolio_ticker.currency
            )

        # --- Si update : soustraire ancienne valeur
        if old_tx and old_tx.portfolio.name != PORTFOLIO_MAIN_NAME:
            old_global_ticker = None
            if old_tx.portfolio_ticker:
                old_global_ticker = PortfolioTicker.objects.filter(
                    portfolio=global_portfolio,
                    ticker=old_tx.portfolio_ticker.ticker,
                    currency=old_tx.portfolio_ticker.currency
                ).first()

            match = PortfolioTransaction.objects.filter(
                user=self.user,
                portfolio=global_portfolio,
                portfolio_ticker=old_global_ticker,
                operation=old_tx.operation,
                date=old_tx.date,
                stock_price=old_tx.stock_price,
                currency=old_tx.currency,
            ).first()

            if match:
                match.amount -= old_tx.amount
                match.fees -= old_tx.fees
                match.quantity = (match.quantity or 0) - (old_tx.quantity or 0)
                if match.amount <= 0:
                    match.delete()
                else:
                    match.save()

        # --- Ajouter la version courante
        match = PortfolioTransaction.objects.filter(
            user=self.user,
            portfolio=global_portfolio,
            portfolio_ticker=global_ticker,
            operation=self.operation,
            date=self.date,
            stock_price=self.stock_price,
            currency=self.currency,
        ).first()

        if match:
            match.amount += self.amount
            match.fees += self.fees
            match.quantity = (match.quantity or 0) + (self.quantity or 0)
            match.save()
        else:
            PortfolioTransaction.objects.create(
                user=self.user,
                portfolio=global_portfolio,
                portfolio_ticker=global_ticker,
                operation=self.operation,
                date=self.date,
                amount=self.amount,
                fees=self.fees,
                stock_price=self.stock_price,
                quantity=self.quantity,
                currency=self.currency
            )

    def delete(self, *args, **kwargs):
        if self.portfolio.name != PORTFOLIO_MAIN_NAME:
            global_portfolio = Portfolio.objects.get(user=self.user, name=PORTFOLIO_MAIN_NAME)

            global_ticker = None
            if self.portfolio_ticker:
                global_ticker = PortfolioTicker.objects.filter(
                    portfolio=global_portfolio,
                    ticker=self.portfolio_ticker.ticker,
                    currency=self.portfolio_ticker.currency
                ).first()

            match = PortfolioTransaction.objects.filter(
                user=self.user,
                portfolio=global_portfolio,
                portfolio_ticker=global_ticker,
                operation=self.operation,
                date=self.date,
                stock_price=self.stock_price,
                currency=self.currency,
            ).first()

            if match:
                match.amount -= self.amount
                match.fees -= self.fees
                match.quantity = (match.quantity or 0) - (self.quantity or 0)
                if match.amount <= 0:
                    match.delete()
                else:
                    match.save()

        super().delete(*args, **kwargs)

    @classmethod
    def get_transactions_dataframe(cls, user, portfolio, currency: str) -> pd.DataFrame:
        """
        Retourne un DataFrame de toutes les transactions d'un portefeuille
        pour un utilisateur donné et une devise donnée.

        Index = date
        Colonnes = id, portfolio_ticker_id, operation, amount, fees,
                   stock_price, quantity, currency, ticker
        """
        qs = (
            cls.objects.filter(
                user=user,
                portfolio=portfolio,
                currency=currency,
            )
            .select_related("portfolio_ticker__ticker")
            .order_by("date", "id")
        )

        if not qs.exists():
            return pd.DataFrame()

        df = pd.DataFrame.from_records(
            qs.values(
                "id",
                "portfolio_ticker_id",
                "operation",
                "amount",
                "fees",
                "stock_price",
                "quantity",
                "currency",
                "date",
                ticker=models.F("portfolio_ticker__ticker__ticker"),
            )
        )

        df.set_index("date", inplace=True)
        df.index = pd.to_datetime(df.index)

        # Convertir les Decimal en float
        for col in ["amount", "fees", "stock_price", "quantity"]:
            df[col] = df[col].astype(float)

        return StockSplit.apply_splits(df)

    @classmethod
    def get_transactions_in_eur(cls, user, portfolio) -> pd.DataFrame:
        """
        Retourne un DataFrame de toutes les transactions d'un portefeuille
        d'un utilisateur, converties en EUR (basé sur le ticker EURUSD=X).
        """
        qs = (
            cls.objects.filter(user=user, portfolio=portfolio)
            .select_related("portfolio_ticker__ticker")
            .order_by("date", "id")
        )
        if not qs.exists():
            return pd.DataFrame()

        # --- Transactions en DataFrame ---
        df = pd.DataFrame.from_records(
            qs.values(
                "id", "portfolio_ticker_id", "operation", "amount", "fees",
                "stock_price", "quantity", "currency", "date",
                ticker=models.F("portfolio_ticker__ticker__ticker"),
            )
        )
        df.set_index("date", inplace=True)
        df.index = pd.to_datetime(df.index)

        # Convertir les Decimal en float
        for col in ["amount", "fees", "stock_price", "quantity"]:
            df[col] = df[col].astype(float)

        # --- Récupération des taux EURUSD ---
        fx_prices = StockPrice.objects.filter(
            ticker_id="EURUSD=X", date__in=df.index
        ).values("date", "open_price")

        if not fx_prices.exists():
            raise ValueError("Pas de données de change disponibles pour EURUSD=X")

        fx_df = pd.DataFrame.from_records(fx_prices)
        fx_df.set_index("date", inplace=True)
        fx_df.sort_index(inplace=True)
        fx_df = fx_df.astype(float)

        # Assurer couverture de toutes les dates (ffill/bfill pour trous)
        fx_df = fx_df.reindex(df.index).ffill().bfill()

        # --- Conversion en EUR ---
        def convert_row(row):
            if row["currency"] == "EUR":
                return row
            elif row["currency"] == "USD":
                fx_rate = fx_df.loc[row.name, "open_price"]
                # USD → EUR : diviser par le taux
                row["amount"] = row["amount"] / fx_rate
                row["fees"] = row["fees"] / fx_rate
                if row["stock_price"]:
                    row["stock_price"] = row["stock_price"] / fx_rate
            return row

        df = df.apply(convert_row, axis=1)
        df["currency"] = "EUR"

        return StockSplit.apply_splits(df)

    @classmethod
    def first_and_last_date(cls, user, portfolio) -> tuple[datetime | None, datetime | None]:
        """
        Retourne la première et la dernière date de transaction d'un utilisateur
        dans un portefeuille donné. Retourne (None, None) si aucune transaction.
        """
        result = (
            cls.objects.filter(user=user, portfolio=portfolio)
            .aggregate(
                first_date=Min("date"),
                last_date=Max("date")
            )
        )

        first_date = pd.to_datetime(result["first_date"]) if result["first_date"] else None
        last_date = pd.to_datetime(result["last_date"]) if result["last_date"] else None

        return first_date, last_date

    @classmethod
    def get_open_positions_dict(cls, user, portfolio) -> dict[str, pd.DataFrame]:
        """
        Retourne un dictionnaire {ticker: dataframe} ne contenant que les positions ouvertes
        (opérations buy/sell uniquement) d'un utilisateur pour un portefeuille donné.
        Les transactions sont converties en EUR.
        """
        df = cls.get_transactions_in_eur(user, portfolio)

        if df.empty:
            return {}

        # Garder uniquement les opérations buy/sell
        df = df[df["operation"].isin(["buy", "sell"])]

        open_positions = {}

        for ticker, ticker_df in df.groupby("ticker"):
            if ticker is None:  # ignorer dépôts/retraits
                continue

            ticker_df = ticker_df.sort_index()
            qty = 0.0
            last_open_index = None

            for idx, row in ticker_df.iterrows():
                if row["operation"] == "buy":
                    qty += row["quantity"]
                    if last_open_index is None:
                        last_open_index = idx
                elif row["operation"] == "sell":
                    qty -= row["quantity"]

                # si la position est fermée → reset
                if abs(qty) < 1e-9:
                    last_open_index = None

            # si position encore ouverte → garder seulement depuis la dernière ouverture
            if qty > 0 and last_open_index is not None:
                open_positions[ticker] = ticker_df.loc[last_open_index:]

        return open_positions

    @classmethod
    def get_buy_transactions(cls, user_id=None, portfolio_id=None) -> pd.DataFrame:
        """
        Retourne un DataFrame avec les transactions d'achat nettes,
        en tenant compte des ventes partielles ou totales.
        Chaque ligne représente la quantité encore détenue.
        Les montants restent positifs.
        """
        # Récupérer toutes les transactions d'achat et de vente
        qs = cls.objects.filter(operation__in=["buy", "sell"]).select_related("portfolio_ticker__ticker")
        if user_id is not None:
            qs = qs.filter(user_id=user_id)
        if portfolio_id is not None:
            qs = qs.filter(portfolio_id=portfolio_id)

        df = pd.DataFrame.from_records(
            qs.values(
                "date", "amount", "operation", "fees", "stock_price",
                "quantity", "currency", "portfolio_ticker__ticker__ticker"
            )
        )

        if df.empty:
            return pd.DataFrame()

        df["date"] = pd.to_datetime(df["date"])
        df.sort_values("date", inplace=True)

        def compute_remaining_transactions(group):
            group = group.copy()
            remaining_transactions = []

            for _, row in group.iterrows():
                qty = row["quantity"]
                if row["operation"] == "buy":
                    remaining_transactions.append(row.to_dict())
                elif row["operation"] == "sell":
                    # On réduit la quantité des achats précédents
                    qty_to_sell = qty
                    for prev in remaining_transactions:
                        if prev["quantity"] >= qty_to_sell:
                            prev["quantity"] -= qty_to_sell
                            qty_to_sell = 0
                            break
                        else:
                            qty_to_sell -= prev["quantity"]
                            prev["quantity"] = 0
                    # Supprimer les transactions complètement vendues
                    remaining_transactions = [t for t in remaining_transactions if t["quantity"] > 0]

            return pd.DataFrame(remaining_transactions)

        df = df.groupby("portfolio_ticker__ticker__ticker", group_keys=False).apply(compute_remaining_transactions)

        if df.empty:
            return df

        df.rename(columns={"portfolio_ticker__ticker__ticker": "ticker"}, inplace=True)
        df.set_index("date", inplace=True)

        numeric_cols = ["amount", "fees", "stock_price", "quantity"]
        for col in numeric_cols:
            df[col] = df[col].astype(float)

        return StockSplit.apply_splits(df)


class PortfolioPerformance(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE)
    calculated_at = models.DateTimeField(auto_now=True)

    tickers_invested_amounts = models.JSONField()
    tickers_twr = models.JSONField()
    tickers_gain = models.JSONField()
    tickers_valuation = models.JSONField()
    tickers_dividends = models.JSONField()
    tickers_pru = models.JSONField()

    portfolio_twr = models.JSONField()
    portfolio_gain = models.JSONField()
    portfolio_monthly_percentages = models.JSONField()
    portfolio_valuation = models.JSONField()
    portfolio_invested_amounts = models.JSONField()
    
    portfolio_cash = models.JSONField()
    portfolio_fees = models.JSONField()
    portfolio_cagr = models.JSONField()
    portfolio_dividend_yield = models.JSONField()
    portfolio_dividend_earn = models.JSONField()

class TransactionCompareSP500(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE)
    calculated_at = models.DateTimeField(auto_now=True)
    ticker = models.ForeignKey(PortfolioTicker, on_delete=models.CASCADE, blank=True, null=True)

    date = models.DateField(blank=True, null=True)
    purchase_amount = models.DecimalField(max_digits=12, decimal_places=2)
    current_value = models.DecimalField(max_digits=12, decimal_places=2)
    total_gain = models.DecimalField(max_digits=12, decimal_places=2)
    gain_percentage = models.DecimalField(max_digits=12, decimal_places=2)
    sp500_value = models.DecimalField(max_digits=12, decimal_places=2)
    sp500_gain_percentage = models.DecimalField(max_digits=12, decimal_places=2)
    performance_gap = models.DecimalField(max_digits=12, decimal_places=2)
    holding_duration = models.DecimalField(max_digits=12, decimal_places=2)
    annualized_return = models.DecimalField(max_digits=12, decimal_places=2)
    dividend_amount = models.DecimalField(max_digits=12, decimal_places=2)
    dividend_yield = models.DecimalField(max_digits=12, decimal_places=2)
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    stock_price = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_fees = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, blank=True, null=True)

    @classmethod
    def create_or_update_transaction(
        cls,
        user,
        portfolio,
        ticker,
        date,
        purchase_amount,
        current_value,
        total_gain,
        gain_percentage,
        sp500_value,
        sp500_gain_percentage,
        performance_gap,
        holding_duration,
        annualized_return,
        dividend_amount,
        dividend_yield,
        quantity,
        stock_price,
        transaction_fees,
        currency,
        tolerance: Decimal = Decimal("0.01")
    ):
        """
        Crée ou met à jour une transaction comparée au SP500.
        Si une transaction proche existe (tolérance), elle sera remplacée.
        """

        # Recherche d'une transaction existante proche
        existing_qs = cls.objects.filter(
            user=user,
            portfolio=portfolio,
            ticker=ticker,
            date=date
        ).filter(
            purchase_amount__gte=purchase_amount - tolerance,
            purchase_amount__lte=purchase_amount + tolerance,
            quantity__gte=quantity - tolerance,
            quantity__lte=quantity + tolerance,
            stock_price__gte=stock_price - tolerance,
            stock_price__lte=stock_price + tolerance
        )

        if existing_qs.exists():
            # Met à jour la transaction existante
            existing_qs.update(
                purchase_amount=purchase_amount,
                current_value=current_value,
                total_gain=total_gain,
                gain_percentage=gain_percentage,
                sp500_value=sp500_value,
                sp500_gain_percentage=sp500_gain_percentage,
                performance_gap=performance_gap,
                holding_duration=holding_duration,
                annualized_return=annualized_return,
                dividend_amount=dividend_amount,
                dividend_yield=dividend_yield,
                quantity=quantity,
                stock_price=stock_price,
                transaction_fees=transaction_fees,
                currency=currency,
            )
            return existing_qs.first()

        # Sinon, création d'une nouvelle transaction
        transaction = cls.objects.create(
            user=user,
            portfolio=portfolio,
            ticker=ticker,
            date=date,
            purchase_amount=purchase_amount,
            current_value=current_value,
            total_gain=total_gain,
            gain_percentage=gain_percentage,
            sp500_value=sp500_value,
            sp500_gain_percentage=sp500_gain_percentage,
            performance_gap=performance_gap,
            holding_duration=holding_duration,
            annualized_return=annualized_return,
            dividend_amount=dividend_amount,
            dividend_yield=dividend_yield,
            quantity=quantity,
            stock_price=stock_price,
            transaction_fees=transaction_fees,
            currency=currency,
        )
        return transaction

class TickerPerformanceCompareSP500(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE)
    ticker = models.ForeignKey(PortfolioTicker, on_delete=models.CASCADE, blank=True, null=True)

    calculated_at = models.DateTimeField(auto_now=True)
    number_of_transactions = models.DecimalField(max_digits=12, decimal_places=2)
    purchase_amount = models.DecimalField(max_digits=12, decimal_places=2)
    current_value = models.DecimalField(max_digits=12, decimal_places=2)
    total_gain = models.DecimalField(max_digits=12, decimal_places=2)
    gain_percentage = models.DecimalField(max_digits=12, decimal_places=2)
    sp500_value = models.DecimalField(max_digits=12, decimal_places=2)
    sp500_gain_percentage = models.DecimalField(max_digits=12, decimal_places=2)
    performance_gap = models.DecimalField(max_digits=12, decimal_places=2)
    holding_duration = models.DecimalField(max_digits=12, decimal_places=2)
    annualized_return = models.DecimalField(max_digits=12, decimal_places=2)
    dividend_amount = models.DecimalField(max_digits=12, decimal_places=2)
    dividend_yield = models.DecimalField(max_digits=12, decimal_places=2)
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_fees = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, blank=True, null=True)

    @classmethod
    def create_or_update_transaction(
        cls,
        user,
        portfolio,
        ticker,
        number_of_transactions,
        purchase_amount,
        current_value,
        total_gain,
        gain_percentage,
        sp500_value,
        sp500_gain_percentage,
        performance_gap,
        holding_duration,
        annualized_return,
        dividend_amount,
        dividend_yield,
        quantity,
        transaction_fees,
        currency,
        tolerance: Decimal = Decimal("0.01")
    ):
        """
        Crée ou met à jour une performance agrégée par ticker comparée au SP500.
        Si elle existe déjà (avec tolérance), elle sera remplacée.
        """
        existing_qs = cls.objects.filter(
            user=user,
            portfolio=portfolio,
            ticker=ticker,
            number_of_transactions__gte=number_of_transactions - tolerance,
            number_of_transactions__lte=number_of_transactions + tolerance,
            purchase_amount__gte=purchase_amount - tolerance,
            purchase_amount__lte=purchase_amount + tolerance,
            current_value__gte=current_value - tolerance,
            current_value__lte=current_value + tolerance,
            total_gain__gte=total_gain - tolerance,
            total_gain__lte=total_gain + tolerance,
            gain_percentage__gte=gain_percentage - tolerance,
            gain_percentage__lte=gain_percentage + tolerance,
            sp500_value__gte=sp500_value - tolerance,
            sp500_value__lte=sp500_value + tolerance,
            sp500_gain_percentage__gte=sp500_gain_percentage - tolerance,
            sp500_gain_percentage__lte=sp500_gain_percentage + tolerance,
            performance_gap__gte=performance_gap - tolerance,
            performance_gap__lte=performance_gap + tolerance,
            holding_duration__gte=holding_duration - tolerance,
            holding_duration__lte=holding_duration + tolerance,
            annualized_return__gte=annualized_return - tolerance,
            annualized_return__lte=annualized_return + tolerance,
            dividend_amount__gte=dividend_amount - tolerance,
            dividend_amount__lte=dividend_amount + tolerance,
            dividend_yield__gte=dividend_yield - tolerance,
            dividend_yield__lte=dividend_yield + tolerance,
            quantity__gte=quantity - tolerance,
            quantity__lte=quantity + tolerance,
            transaction_fees__gte=transaction_fees - tolerance,
            transaction_fees__lte=transaction_fees + tolerance,
            currency=currency,
        )

        if existing_qs.exists():
            # Met à jour la performance existante
            existing_qs.update(
                number_of_transactions=number_of_transactions,
                purchase_amount=purchase_amount,
                current_value=current_value,
                total_gain=total_gain,
                gain_percentage=gain_percentage,
                sp500_value=sp500_value,
                sp500_gain_percentage=sp500_gain_percentage,
                performance_gap=performance_gap,
                holding_duration=holding_duration,
                annualized_return=annualized_return,
                dividend_amount=dividend_amount,
                dividend_yield=dividend_yield,
                quantity=quantity,
                transaction_fees=transaction_fees,
            )
            return existing_qs.first()

        # Sinon, crée une nouvelle performance
        ticker_performance = cls.objects.create(
            user=user,
            portfolio=portfolio,
            ticker=ticker,
            number_of_transactions=number_of_transactions,
            purchase_amount=purchase_amount,
            current_value=current_value,
            total_gain=total_gain,
            gain_percentage=gain_percentage,
            sp500_value=sp500_value,
            sp500_gain_percentage=sp500_gain_percentage,
            performance_gap=performance_gap,
            holding_duration=holding_duration,
            annualized_return=annualized_return,
            dividend_amount=dividend_amount,
            dividend_yield=dividend_yield,
            quantity=quantity,
            transaction_fees=transaction_fees,
            currency=currency,
        )
        return ticker_performance
