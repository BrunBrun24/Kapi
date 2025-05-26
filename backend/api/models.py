from typing import Type
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from django.conf import settings


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

class UserPreference(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return f"Préférences de {self.user.email}"

class Portfolio(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.user.email} - {self.name}"

    @property
    def authorized_tickers(self):
        return self.portfolioticker_set.all()

    @classmethod
    def get_user_portfolios(cls: Type['Portfolio'], user):
        return cls.objects.filter(user=user)

class PortfolioTicker(models.Model):
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE)
    ticker = models.ForeignKey(Company, on_delete=models.CASCADE, to_field='ticker', db_column='ticker')
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES)

    class Meta:
        unique_together = ("portfolio", "ticker")

    def __str__(self):
        return f"{self.portfolio.name} - {self.ticker}"

class PortfolioTransaction(models.Model):
    OPERATION_CHOICES = [
        ('buy', 'Achat'),
        ('sell', 'Vente'),
        ('dividend', 'Dividende'),
        ('interest', 'Intérêt'),
        ('deposit', "Dépôt"),
        ('withdrawal', "Retrait"),
    ]

    portfolio_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
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
        return f"{self.operation.upper()} - {self.portfolio_ticker.ticker} - {self.quantity}"

    @classmethod
    def get_user_portfolios(cls, user):
        return cls.objects.filter(portfolio_user=user)

