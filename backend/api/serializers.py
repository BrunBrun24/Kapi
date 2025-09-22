from rest_framework import serializers
from .models import (
    CURRENCY_CHOICES, CustomUser, Portfolio, PortfolioTicker, PortfolioTransaction
)


# -------------------- UTILISATEUR --------------------
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


# -------------------- PORTEFEUILLE --------------------
class PortfolioSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour la création et la récupération de portefeuilles.
    Le champ 'user' est automatiquement défini à partir de la requête.
    """
    class Meta:
        model = Portfolio
        fields = ["id", "name"]
        read_only_fields = ["id"]

    def create(self, validated_data):
        user = self.context["request"].user
        return Portfolio.objects.create(user=user, **validated_data)

    def update(self, instance, validated_data):
        instance.name = validated_data.get("name", instance.name)
        instance.save()
        return instance


# -------------------- PORTEFEUILLE TICKER --------------------
class PortfolioTickerSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortfolioTicker
        fields = ["ticker", "currency"]

    def change_currency(self, new_currency):
        self.instance.currency = new_currency
        self.instance.save()


# -------------------- TRANSACTIONS --------------------
class PortfolioTransactionBaseSerializer(serializers.ModelSerializer):
    """
    Sérialiseur commun pour la création et mise à jour des transactions.
    Contient la validation factorisée.
    """

    def _round(self, value, decimals=2):
        return round(float(value or 0), decimals)

    def _validate_transaction_fields(self, portfolio, operation, portfolio_ticker, stock_price, quantity, currency):
        user = self.context['request'].user
        if portfolio.user != user:
            raise serializers.ValidationError("Ce portefeuille ne vous appartient pas.")

        if operation in ["buy", "sell"]:
            if not portfolio_ticker or stock_price is None:
                raise serializers.ValidationError("Le ticker et le prix sont requis pour un achat ou une vente.")
            if not currency:
                raise serializers.ValidationError("La devise est requise pour un achat ou une vente.")

        elif operation == "dividend":
            if not portfolio_ticker or quantity is None:
                raise serializers.ValidationError("Le ticker et la quantité sont requis pour un dividende.")
            if not currency:
                raise serializers.ValidationError("La devise est requise pour un dividende.")

        elif operation == "interest":
            if portfolio_ticker:
                raise serializers.ValidationError("Le ticker ne doit pas être renseigné pour un intérêt.")
            if not currency:
                raise serializers.ValidationError("La devise est requise pour un intérêt.")

        elif operation in ["deposit", "withdrawal"]:
            if not currency:
                raise serializers.ValidationError("La devise est requise pour un dépôt ou un retrait.")
            if portfolio_ticker:
                raise serializers.ValidationError("Le ticker ne doit pas être renseigné pour un dépôt ou un retrait.")


# -------------------- CREATE --------------------
class PortfolioTransactionCreateSerializer(PortfolioTransactionBaseSerializer):
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
        portfolio = data.get("portfolio")
        operation = data.get("operation")
        portfolio_ticker = data.get("portfolio_ticker")
        stock_price = data.get("stock_price")
        quantity = data.get("quantity")
        currency = data.get("currency")

        self._validate_transaction_fields(portfolio, operation, portfolio_ticker, stock_price, quantity, currency)
        return data


# -------------------- UPDATE --------------------
class PortfolioTransactionUpdateSerializer(PortfolioTransactionBaseSerializer):
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
        portfolio = data.get("portfolio", getattr(self.instance, "portfolio"))
        operation = data.get("operation", getattr(self.instance, "operation"))
        portfolio_ticker = data.get("portfolio_ticker", getattr(self.instance, "portfolio_ticker"))
        stock_price = data.get("stock_price", getattr(self.instance, "stock_price"))
        quantity = data.get("quantity", getattr(self.instance, "quantity"))
        currency = data.get("currency", getattr(self.instance, "currency"))

        self._validate_transaction_fields(portfolio, operation, portfolio_ticker, stock_price, quantity, currency)
        return data
