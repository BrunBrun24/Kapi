from rest_framework import serializers
from .models import (
    CustomUser, Company, StockPrice, UserPreference,
    Portfolio, PortfolioTicker, PortfolioTransaction,
    PortfolioDepositOfMoney
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



# Transaction
class PortfolioTransactionCreateSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour la création d'une transaction dans un portefeuille.
    L'utilisateur est lié automatiquement à partir de la requête.
    """
    class Meta:
        model = PortfolioTransaction
        fields = [
            'portfolio_user', 'portfolio_ticker', 'operation', 'stock_price', 'date',
            'amount', 'quantity', 'fees', 'notes'
        ]
        read_only_fields = ['portfolio_user']

    def create(self, validated_data):
        validated_data['portfolio_user'] = self.context['request'].user
        return super().create(validated_data)

class PortfolioTransactionDetailSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour afficher une transaction avec des informations enrichies
    (nom de l’action, ticker, et arrondis numériques pour les montants).
    """
    ticker = serializers.CharField(source='portfolio_ticker.ticker')
    name = serializers.CharField(source='portfolio_ticker.ticker.name')
    stock_price = serializers.SerializerMethodField()
    fees = serializers.SerializerMethodField()
    amount = serializers.SerializerMethodField()
    quantity = serializers.SerializerMethodField()

    class Meta:
        model = PortfolioTransaction
        fields = [
            'operation', 'stock_price', 'date',
            'amount', 'quantity', 'fees', 'name', 'ticker', 'id'
        ]

    def get_stock_price(self, obj):
        return round(float(obj.stock_price), 2)

    def get_fees(self, obj):
        return round(float(obj.fees), 2)
    
    def get_amount(self, obj):
        return round(float(obj.amount), 2)

    def get_quantity(self, obj):
        return round(float(obj.quantity), 2)

class PortfolioTransactionUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortfolioTransaction
        fields = [
            'portfolio_ticker',
            'operation',
            'stock_price',
            'date',
            'amount',
            'quantity',
            'fees',
            'notes',
        ]
        read_only_fields = ['portfolio_user']

    def validate(self, attrs):
        operation = attrs.get('operation')
        if operation not in dict(PortfolioTransaction.OPERATION_CHOICES):
            raise serializers.ValidationError({"operation": "Opération invalide."})
        return attrs
    
    def get_queryset(self):
        return PortfolioTransaction.objects.filter(portfolio_user=self.request.user)
