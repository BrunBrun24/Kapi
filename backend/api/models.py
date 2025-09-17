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
    date = models.DateField()
    open_price = models.DecimalField(max_digits=12, decimal_places=6)
    high_price = models.DecimalField(max_digits=12, decimal_places=6)
    low_price = models.DecimalField(max_digits=12, decimal_places=6)
    close_price = models.DecimalField(max_digits=12, decimal_places=6)
    volume = models.BigIntegerField()

    class Meta:
        unique_together = ("ticker", "date")
        indexes = [models.Index(fields=["ticker"]), models.Index(fields=["date"])]

    def __str__(self):
        return f"{self.ticker} - {self.date}"

    # ------------------ Méthodes pour DataFrame ------------------

    @classmethod
    def _build_open_price_dataframe(cls, prices_queryset) -> pd.DataFrame:
        """Transforme un queryset de StockPrice en DataFrame pivoté indexé par date."""
        if not prices_queryset.exists():
            return pd.DataFrame()
        df = pd.DataFrame.from_records(prices_queryset.values("date", "ticker_id", "open_price"))
        df_pivot = df.pivot(index="date", columns="ticker_id", values="open_price")
        df_pivot.sort_index(inplace=True)
        df_pivot.index = pd.to_datetime(df_pivot.index)
        return df_pivot.astype(float)

    @classmethod
    def get_open_prices_dataframe_for_all_users(cls) -> pd.DataFrame:
        tickers = PortfolioTicker.objects.values_list('ticker__ticker', flat=True).distinct()
        prices = cls.objects.filter(ticker_id__in=tickers)
        return cls._build_open_price_dataframe(prices)

    @classmethod
    def get_open_prices_dataframe_for_user(cls, user: CustomUser) -> pd.DataFrame:
        tickers = PortfolioTicker.objects.filter(portfolio__user=user).values_list('ticker__ticker', flat=True).distinct()
        prices = cls.objects.filter(ticker_id__in=tickers)
        return cls._build_open_price_dataframe(prices)

    @classmethod
    def get_open_prices_dataframe_for_user_start_date(cls, user: CustomUser, start_date: datetime) -> pd.DataFrame:
        tickers = PortfolioTicker.objects.filter(portfolio__user=user).values_list('ticker__ticker', flat=True).distinct()
        prices = cls.objects.filter(ticker_id__in=tickers, date__gte=(start_date - timedelta(days=3)))
        return cls._build_open_price_dataframe(prices)

    @classmethod
    def get_open_prices_dataframe_for_tickers(cls, tickers: list[str]) -> pd.DataFrame:
        if not tickers:
            return pd.DataFrame()
        prices = cls.objects.filter(ticker_id__in=tickers)
        return cls._build_open_price_dataframe(prices)

    @classmethod
    def get_open_prices_dataframe_for_ticker(cls, ticker: str) -> pd.DataFrame:
        if not ticker:
            return pd.DataFrame()
        prices = cls.objects.filter(ticker_id=ticker)
        return cls._build_open_price_dataframe(prices)

    # ------------------ Méthodes de conversion ------------------

    @classmethod
    def convert_price(cls, price: float, from_currency: str, to_currency: str, date: datetime) -> float:
        if from_currency == to_currency:
            return price
        fx_obj = cls.objects.filter(ticker_id="EURUSD=X", date__lte=date).order_by("-date").first()
        if not fx_obj:
            raise ValueError(f"Aucun taux de change EURUSD trouvé avant {date}")
        fx_rate = float(fx_obj.open_price)
        return price / fx_rate if from_currency == "USD" and to_currency == "EUR" else price * fx_rate

    @classmethod
    def convert_dataframe_to_currency(cls, df: pd.DataFrame, target_currency: str) -> pd.DataFrame:
        if df.empty:
            return df
        if target_currency not in ["USD", "EUR"]:
            raise ValueError("La devise cible doit être USD ou EUR")
        tickers_currencies = dict(Company.objects.filter(ticker__in=df.columns).values_list("ticker", "currency"))
        fx_df = cls._build_open_price_dataframe(cls.objects.filter(ticker_id="EURUSD=X", date__in=df.index))
        fx_df = fx_df.reindex(df.index).ffill().bfill()
        converted_df = df.copy()
        for ticker in df.columns:
            cur = tickers_currencies.get(ticker)
            if cur and cur != target_currency:
                converted_df[ticker] = cls.convert_price(df[ticker], cur, target_currency, df.index[-1])
        return converted_df

    @classmethod
    def get_price_on_date(cls, ticker: str, date: datetime, target_currency: str) -> float:
        stock = cls.objects.filter(ticker_id=ticker, date__lte=date).order_by("-date").first()
        if not stock:
            raise ValueError(f"Pas de prix pour {ticker} avant {date}")
        ticker_currency = Company.objects.get(ticker=ticker).currency
        return cls.convert_price(float(stock.open_price), ticker_currency, target_currency, date)

class StockSplit(models.Model):
    ticker = models.ForeignKey(Company, on_delete=models.CASCADE, to_field="ticker", db_column="ticker")
    date = models.DateField()
    split_ratio = models.FloatField()

    class Meta:
        unique_together = ("ticker", "date")
        indexes = [models.Index(fields=["ticker", "date"])]

    def __str__(self):
        return f"{self.ticker.ticker} - {self.date} : {self.split_ratio}"

    @staticmethod
    def get_splits_from_db(tickers: list[str]) -> dict:
        """
        Récupère les splits depuis la base pour une liste de tickers.
        Retourne un dict {ticker: pd.Series(index=date, values=split_ratio)}.
        """
        splits = (
            StockSplit.objects
            .filter(ticker__ticker__in=tickers)
            .values_list("ticker__ticker", "date", "split_ratio")
            .order_by("ticker__ticker", "date")
        )

        grouped = defaultdict(list)
        for ticker, date, ratio in splits:
            grouped[ticker].append((pd.to_datetime(date), ratio))

        return {
            ticker: pd.Series([ratio for d, ratio in values], index=[d for d, ratio in values])
            for ticker, values in grouped.items()
        }

    @classmethod
    def apply_splits(cls, transactions: pd.DataFrame) -> pd.DataFrame:
        """
        Ajuste 'quantity' et 'stock_price' en fonction des splits.
        Index du DataFrame = date de transaction.
        """
        if transactions.empty:
            return transactions

        required = {"ticker", "quantity", "stock_price"}
        if not required.issubset(transactions.columns):
            raise ValueError(f"Le DataFrame doit contenir les colonnes {required}")

        tickers = transactions["ticker"].dropna().unique().tolist()
        splits_dict = cls.get_splits_from_db(tickers)

        def adjust_row(row):
            ticker = row["ticker"]
            if ticker not in splits_dict:
                return row[["quantity", "stock_price"]]

            date_tx = row.name  # index = date
            splits = splits_dict[ticker]
            future_splits = splits[splits.index > date_tx]

            factor = future_splits.prod() if not future_splits.empty else 1.0
            return pd.Series({
                "quantity": row["quantity"] * factor,
                "stock_price": row["stock_price"] / factor,
            })

        adjustments = transactions.apply(adjust_row, axis=1)
        transactions.update(adjustments)

        return transactions

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
        indexes = [models.Index(fields=["ticker", "date"])]
        verbose_name = "Dividende"
        verbose_name_plural = "Dividendes"

    def __str__(self):
        return f"{self.ticker.ticker} - {self.date} : {self.amount}"

    @staticmethod
    def _to_dividends_df(queryset, single_ticker: str | None = None) -> pd.DataFrame:
        """
        Transforme un queryset de dividendes en DataFrame formaté.
        - Index = date
        - Colonnes = tickers (ou une seule colonne si single_ticker)
        """
        df = pd.DataFrame.from_records(
            queryset.values("date", "ticker__ticker", "amount")
        )
        if df.empty:
            return df

        df.rename(columns={"ticker__ticker": "ticker"}, inplace=True)
        df["date"] = pd.to_datetime(df["date"])

        if single_ticker:
            df = df[["date", "amount"]].set_index("date")
            df = df.astype(float).rename(columns={"amount": single_ticker})
        else:
            df = df.pivot(index="date", columns="ticker", values="amount")
            df = df.astype(float)

        df.sort_index(inplace=True)
        return df

    @classmethod
    def get_dividends_for_ticker(cls, ticker: str) -> pd.DataFrame:
        qs = cls.objects.filter(ticker__ticker=ticker)
        return cls._to_dividends_df(qs, single_ticker=ticker)

    @classmethod
    def get_dividends_for_tickers(cls, tickers: list[str]) -> pd.DataFrame:
        if not tickers:
            return pd.DataFrame()
        qs = cls.objects.filter(ticker__ticker__in=tickers)
        return cls._to_dividends_df(qs)

    @classmethod
    def get_dividends_for_tickers_between_dates(
        cls, tickers: list[str], start_date: datetime, end_date: datetime
    ) -> pd.DataFrame:
        if not tickers:
            return pd.DataFrame()
        qs = cls.objects.filter(
            ticker__ticker__in=tickers,
            date__gte=start_date,
            date__lte=end_date
        )
        return cls._to_dividends_df(qs)

class Portfolio(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=20)

    def __str__(self) -> str:
        return f"{self.user.email} - {self.name}"

    @classmethod
    def get_user_portfolios(cls: Type['Portfolio'], user):
        """Retourne tous les portefeuilles d'un utilisateur."""
        return cls.objects.filter(user=user)

    def save(self, *args, **kwargs):
        """Sauvegarde et crée le portefeuille principal si nécessaire."""
        is_new = self._state.adding
        super().save(*args, **kwargs)

        if is_new and not Portfolio.objects.filter(user=self.user, name=PORTFOLIO_MAIN_NAME).exists():
            Portfolio.objects.create(user=self.user, name=PORTFOLIO_MAIN_NAME)

    @classmethod
    def get_user_portfolio_name(cls, user_id: int, portfolio_id: int) -> str | None:
        """Retourne le nom d’un portefeuille par ID utilisateur et ID portefeuille."""
        return (
            cls.objects.filter(pk=portfolio_id, user_id=user_id)
            .values_list("name", flat=True)
            .first()
        )

class PortfolioTicker(models.Model):
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE)
    ticker = models.ForeignKey(Company, on_delete=models.CASCADE, to_field="ticker", db_column="ticker")
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES)

    class Meta:
        unique_together = ("portfolio", "ticker", "currency")

    def __str__(self):
        return f"{self.portfolio.name} - {self.ticker} - {self.currency}"

    def save(self, *args, **kwargs):
        """Ajoute automatiquement le ticker dans le portefeuille global si besoin."""
        is_new = self._state.adding
        super().save(*args, **kwargs)

        if is_new and self.portfolio.name != PORTFOLIO_MAIN_NAME:
            global_portfolio, _ = Portfolio.objects.get_or_create(
                user=self.portfolio.user,
                name=PORTFOLIO_MAIN_NAME,
            )
            if not PortfolioTicker.objects.filter(
                portfolio=global_portfolio,
                ticker=self.ticker,
                currency=self.currency,
            ).exists():
                PortfolioTicker.objects.create(
                    portfolio=global_portfolio,
                    ticker=self.ticker,
                    currency=self.currency,
                )

    def delete(self, *args, **kwargs):
        """Supprime le ticker global uniquement s’il n’est plus utilisé ailleurs et sans transaction."""
        if self.portfolio.name != PORTFOLIO_MAIN_NAME:
            user = self.portfolio.user
            global_portfolio = Portfolio.objects.get(user=user, name=PORTFOLIO_MAIN_NAME)

            global_ticker = PortfolioTicker.objects.filter(
                portfolio=global_portfolio,
                ticker=self.ticker,
                currency=self.currency,
            ).first()

            if global_ticker:
                still_used_elsewhere = PortfolioTicker.objects.filter(
                    portfolio__user=user,
                    ticker=self.ticker,
                    currency=self.currency,
                ).exclude(
                    portfolio__name=PORTFOLIO_MAIN_NAME
                ).exclude(pk=self.pk).exists()

                if not still_used_elsewhere and not PortfolioTransaction.objects.filter(
                    portfolio=global_portfolio,
                    portfolio_ticker=global_ticker,
                ).exists():
                    global_ticker.delete()

        super().delete(*args, **kwargs)

    @classmethod
    def get_all_unique_tickers(cls) -> list[str]:
        """Retourne tous les tickers uniques (codes) pour tous les utilisateurs."""
        return list(
            cls.objects.values_list("ticker__ticker", flat=True).distinct()
        )

    @classmethod
    def get_user_unique_tickers(cls, user) -> list[str]:
        """Retourne tous les tickers uniques (codes) pour un utilisateur donné."""
        return list(
            cls.objects.filter(portfolio__user=user)
            .values_list("ticker__ticker", flat=True)
            .distinct()
        )

    @classmethod
    def get_user_tickers_by_currency(cls, user_id: int, portfolio_id: int) -> dict[str, list[str]]:
        """Retourne les tickers groupés par devise pour un portefeuille donné."""
        tickers = (
            cls.objects.filter(portfolio__user_id=user_id, portfolio_id=portfolio_id)
            .values("ticker__ticker", "currency")
            .distinct()
        )
        result: dict[str, list[str]] = {}
        for t in tickers:
            result.setdefault(t["currency"], []).append(t["ticker__ticker"])
        return result

    @classmethod
    def get_currencies_for_ticker(cls, user_id: int, portfolio_id: int, ticker: str) -> list[str]:
        """Retourne la liste des devises associées à un ticker pour un portefeuille donné."""
        return list(
            cls.objects.filter(
                portfolio__user_id=user_id,
                portfolio_id=portfolio_id,
                ticker__ticker=ticker,
            )
            .values_list("currency", flat=True)
            .distinct()
        )

class PortfolioTransaction(models.Model):
    OPERATION_CHOICES = [
        ("buy", "Achat"),
        ("sell", "Vente"),
        ("dividend", "Dividende"),
        ("interest", "Intérêt"),
        ("deposit", "Dépôt"),
        ("withdrawal", "Retrait"),
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
        return cls.objects.filter(portfolio=portfolio).aggregate(total_fees=Sum("fees"))["total_fees"] or 0

    def _get_global_portfolio(self):
        """Retourne le portefeuille global associé à l’utilisateur."""
        return Portfolio.objects.get_or_create(user=self.user, name=PORTFOLIO_MAIN_NAME)[0]

    def _get_global_ticker(self, global_portfolio):
        """Retourne ou crée le ticker dans le portefeuille global."""
        if not self.portfolio_ticker:
            return None
        return PortfolioTicker.objects.get_or_create(
            portfolio=global_portfolio,
            ticker=self.portfolio_ticker.ticker,
            currency=self.portfolio_ticker.currency,
        )[0]

    def _sync_with_global(self, old_tx=None, is_delete=False):
        """Synchronise la transaction avec le portefeuille global."""
        if self.portfolio.name == PORTFOLIO_MAIN_NAME:
            return

        global_portfolio = self._get_global_portfolio()
        global_ticker = self._get_global_ticker(global_portfolio)

        def adjust_global(tx, factor=1):
            """Ajoute ou soustrait une transaction dans le global."""
            match = PortfolioTransaction.objects.filter(
                user=self.user,
                portfolio=global_portfolio,
                portfolio_ticker=global_ticker,
                operation=tx.operation,
                date=tx.date,
                stock_price=tx.stock_price,
                currency=tx.currency,
            ).first()

            if match:
                match.amount += factor * tx.amount
                match.fees += factor * tx.fees
                match.quantity = (match.quantity or 0) + factor * (tx.quantity or 0)
                if match.amount <= 0:
                    match.delete()
                else:
                    match.save()
            elif factor > 0:  # uniquement création
                PortfolioTransaction.objects.create(
                    user=self.user,
                    portfolio=global_portfolio,
                    portfolio_ticker=global_ticker,
                    operation=tx.operation,
                    date=tx.date,
                    amount=tx.amount,
                    fees=tx.fees,
                    stock_price=tx.stock_price,
                    quantity=tx.quantity,
                    currency=tx.currency,
                )

        # Si update ou delete → enlever ancienne version
        if old_tx:
            adjust_global(old_tx, factor=-1)

        # Si création ou update → ajouter nouvelle version
        if not is_delete:
            adjust_global(self, factor=1)

    def save(self, *args, **kwargs):
        old_tx = None
        if self.pk:
            try:
                old_tx = PortfolioTransaction.objects.get(pk=self.pk)
            except PortfolioTransaction.DoesNotExist:
                pass

        super().save(*args, **kwargs)
        self._sync_with_global(old_tx=old_tx, is_delete=False)

    def delete(self, *args, **kwargs):
        self._sync_with_global(old_tx=self, is_delete=True)
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
    last_calculated_at = models.DateTimeField(auto_now=True)

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
    last_calculated_at = models.DateTimeField(auto_now=True)
    ticker = models.ForeignKey(PortfolioTicker, on_delete=models.CASCADE)

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
    ticker = models.ForeignKey(PortfolioTicker, on_delete=models.CASCADE)

    last_calculated_at = models.DateTimeField(auto_now=True)
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
