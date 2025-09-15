from rest_framework import serializers
from .models import (
    CURRENCY_CHOICES, CustomUser, Company, StockPrice, TickerPerformanceCompareSP500, TransactionCompareSP500, UserPreference,
    Portfolio, PortfolioTicker, PortfolioTransaction
)


# Utilisateur
class UserSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour la création d'un utilisateur avec email et mot de passe.
    Le mot de passe est en écriture seule et est hashé via `create_user`.
    """
    class Meta:
        model = CustomUser
        fields = ["id", "email", "password"]
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        return CustomUser.objects.create_user(**validated_data)


# Portefeuille
class PortfolioSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour la création et la récupération de portefeuilles.
    Le champ 'user' est automatiquement défini à partir de la requête.
    """
    class Meta:
        model = Portfolio
        fields = ["id", "name"]
        read_only_fields = ["id"]

    def get_fields(self):
        fields = super().get_fields()
        return fields

    def create(self, validated_data):
        user = self.context["request"].user
        return Portfolio.objects.create(user=user, **validated_data)

    def update(self, instance, validated_data):
        instance.name = validated_data.get("name", instance.name)
        instance.save()
        return instance


# Portefeuille Ticker
class PortfolioTickerSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortfolioTicker
        fields = ["portfolio", "ticker", "currency"]

    def change_currency(self, new_currency):
        self.instance.currency = new_currency
        self.instance.save()

# class TransactionCompareSP500Serializer(serializers.ModelSerializer):
#     class Meta:
#         model = TransactionCompareSP500
#         fields = "__all__"

# class TickerPerformanceCompareSP500Serializer(serializers.ModelSerializer):
#     class Meta:
#         model = TickerPerformanceCompareSP500
#         fields = "__all__"


# Transaction
class PortfolioTransactionCreateSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour la création d'une transaction dans un portefeuille.
    L'utilisateur et le portefeuille sont liés automatiquement à partir de la requête.
    """
    portfolio = serializers.PrimaryKeyRelatedField(queryset=Portfolio.objects.all())
    portfolio_ticker = serializers.PrimaryKeyRelatedField(queryset=PortfolioTicker.objects.all(), required=False, allow_null=True)
    stock_price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    quantity = serializers.DecimalField(max_digits=10, decimal_places=6, required=False, allow_null=True)
    currency = serializers.CharField(max_length=3, required=False, allow_null=True)

    class Meta:
        model = PortfolioTransaction
        fields = [
            'user', 'portfolio', 'portfolio_ticker', 'operation', 'stock_price', 'date',
            'amount', 'quantity', 'fees', 'currency'
        ]
        read_only_fields = ['user']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

    def validate(self, data):
        user = self.context['request'].user
        portfolio = data.get("portfolio")

        if portfolio.user != user:
            raise serializers.ValidationError("Ce portefeuille ne vous appartient pas.")

        operation = data.get("operation")

        if operation in ["buy", "sell"]:
            if not data.get("portfolio_ticker") or data.get("stock_price") is None:
                raise serializers.ValidationError("Le ticker et le prix sont requis pour un achat ou une vente.")
            if not data.get("currency"):
                raise serializers.ValidationError("La devise est requise pour un achat ou une vente.")

        elif operation == "dividend":
            if not data.get("portfolio_ticker") or data.get("quantity") is None:
                raise serializers.ValidationError("Le ticker et la quantité sont requis pour un dividende.")
            if not data.get("currency"):
                raise serializers.ValidationError("La devise est requise pour un dividende.")

        elif operation == "interet":
            if data.get("portfolio_ticker"):
                raise serializers.ValidationError("Le ticker ne doit pas être renseigné pour un intérêt.")
            if data.get("quantity") is None:
                raise serializers.ValidationError("La quantité est requise pour un intérêt.")
            if not data.get("currency"):
                raise serializers.ValidationError("La devise est requise pour un intérêt.")

        elif operation in ["deposit", "withdrawal"]:
            if not data.get("currency"):
                raise serializers.ValidationError("La devise est requise pour un dépôt ou un retrait.")
            if data.get("portfolio_ticker"):
                raise serializers.ValidationError("Le ticker ne doit pas être renseigné pour un dépôt ou un retrait.")

        return data

class PortfolioTransactionDetailSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour afficher une transaction avec des informations enrichies
    (nom de l’action, ticker, et arrondis numériques pour les montants).
    """
    portfolio = serializers.StringRelatedField()
    ticker = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    stock_price = serializers.SerializerMethodField()
    fees = serializers.SerializerMethodField()
    amount = serializers.SerializerMethodField()
    quantity = serializers.SerializerMethodField()
    currency = serializers.SerializerMethodField()

    class Meta:
        model = PortfolioTransaction
        fields = [
            'portfolio', 'operation', 'stock_price', 'date', 'currency',
            'amount', 'quantity', 'fees', 'name', 'ticker', 'id'
        ]

    def get_ticker(self, obj):
        if obj.portfolio_ticker and obj.portfolio_ticker.ticker:
            return obj.portfolio_ticker.ticker.ticker
        return ""

    def get_name(self, obj):
        if obj.portfolio_ticker and obj.portfolio_ticker.ticker:
            return obj.portfolio_ticker.ticker.name
        return ""

    def get_currency(self, obj):
        if obj.currency:
            currency_dict = dict(CURRENCY_CHOICES)
            return currency_dict.get(obj.currency, obj.currency or "")
        return ""

    def get_stock_price(self, obj):
        return round(float(obj.stock_price or 0), 2)

    def get_fees(self, obj):
        return round(float(obj.fees), 2)
    
    def get_amount(self, obj):
        return round(float(obj.amount), 2)

    def get_quantity(self, obj):
        return round(float(obj.quantity or 0), 2)

class PortfolioTransactionUpdateSerializer(serializers.ModelSerializer):
    portfolio = serializers.PrimaryKeyRelatedField(queryset=Portfolio.objects.all())
    portfolio_ticker = serializers.PrimaryKeyRelatedField(queryset=PortfolioTicker.objects.all(), required=False, allow_null=True)
    stock_price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    quantity = serializers.DecimalField(max_digits=10, decimal_places=6, required=False, allow_null=True)
    currency = serializers.CharField(max_length=3, required=False, allow_null=True)

    class Meta:
        model = PortfolioTransaction
        fields = [
            'user', 'portfolio', 'portfolio_ticker', 'operation', 'stock_price', 'date',
            'amount', 'quantity', 'fees', 'currency'
        ]
        read_only_fields = ['user']

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

    def validate(self, data):
        user = self.context['request'].user
        portfolio = data.get("portfolio", self.instance.portfolio)
        operation = data.get("operation", self.instance.operation)
        portfolio_ticker = data.get("portfolio_ticker", self.instance.portfolio_ticker)
        stock_price = data.get("stock_price", self.instance.stock_price)
        quantity = data.get("quantity", self.instance.quantity)
        currency = data.get("currency", self.instance.currency)

        if portfolio.user != user:
            raise serializers.ValidationError("Ce portefeuille ne vous appartient pas.")

        if operation in ["buy", "sell"]:
            if not portfolio_ticker or stock_price is None:
                raise serializers.ValidationError("Le ticker et le prix sont requis pour un achat ou une vente.")

        elif operation == "dividend":
            if not portfolio_ticker or quantity is None:
                raise serializers.ValidationError("Le ticker et la quantité sont requis pour un dividende.")

        elif operation == "interet":
            if portfolio_ticker:
                raise serializers.ValidationError("Le ticker ne doit pas être renseigné pour un intérêt.")
            if quantity is None:
                raise serializers.ValidationError("La quantité est requise pour un intérêt.")

        elif operation in ["deposit", "withdrawal"]:
            if not currency:
                raise serializers.ValidationError("La devise est requise pour un dépôt ou un retrait.")
            if portfolio_ticker:
                raise serializers.ValidationError("Le ticker ne doit pas être renseigné pour un dépôt ou un retrait.")

        return data
