from typing import Type
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from django.conf import settings
from django.db.models import Sum

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

class UserPreference(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return f"Préférences de {self.user.email}"

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

class PortfolioPerformance(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE)
    calculated_at = models.DateTimeField(auto_now=True)

    tickers_invested_amounts = models.JSONField()
    tickers_sold_amounts = models.JSONField()
    tickers_twr = models.JSONField()
    tickers_gain = models.JSONField()
    tickers_valuation = models.JSONField()
    ticker_invested_amounts = models.JSONField()
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
