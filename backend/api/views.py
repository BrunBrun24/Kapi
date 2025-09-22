from datetime import datetime
from decimal import Decimal
from io import BytesIO
from django.forms import ValidationError
from django.shortcuts import get_object_or_404
import pandas as pd
from rest_framework import generics, permissions, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Max
from rest_framework import serializers

from api.utils import html_error_response
from api.services.modules.portfolio_performances import PortfolioPerformances

from .models import (
    CURRENCY_CHOICES,
    Company,
    PortfolioPerformance,
    StockPrice,
    TickerPerformanceCompareSP500,
    TransactionCompareSP500,
    Portfolio,
    PortfolioTicker,
    PortfolioTransaction
)

from .serializers import (
    PortfolioTickerSerializer,
    PortfolioSerializer,
    PortfolioTransactionCreateSerializer,
    PortfolioTransactionUpdateSerializer,
    UserSerializer
)

User = get_user_model()
CURRENCY_SYMBOL_MAP = dict(CURRENCY_CHOICES)

# --------------
# Utilisateur
# --------------
class UserCreateView(generics.CreateAPIView):
    """
    Endpoint public permettant de créer un nouvel utilisateur.
    Utilise le serializer UserSerializer pour valider et enregistrer les données.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            print("ERREURS SERIALIZER :", serializer.errors)
            return Response(serializer.errors, status=400)
        self.perform_create(serializer)
        return Response(serializer.data, status=201)


# --------------
# Portefeuille
# --------------
class PortfolioListCreateView(generics.ListCreateAPIView):
    """
    GET  → Liste les portefeuilles de l'utilisateur connecté
    POST → Crée un portefeuille pour l'utilisateur connecté
    """
    serializer_class = PortfolioSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Portfolio.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save()

class PortfolioDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    → Récupère un portefeuille spécifique
    PUT    → Met à jour un portefeuille
    PATCH  → Met à jour partiellement
    DELETE → Supprime un portefeuille
    """
    serializer_class = PortfolioSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Portfolio.objects.filter(user=self.request.user)


# --------------
# Portefeuille Ticker
# --------------
class PortfolioTickerListCreateView(generics.ListCreateAPIView):
    serializer_class = PortfolioTickerSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        portfolio_id = self.kwargs["portfolio_id"]
        return PortfolioTicker.objects.filter(
            portfolio_id=portfolio_id,
            portfolio__user=self.request.user
        )

    def perform_create(self, serializer):
        # Utiliser le portfolio_id de l'URL
        portfolio_id = self.kwargs["portfolio_id"]
        serializer.save(portfolio_id=portfolio_id)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        data = []
        for pt in queryset:
            data.append({
                "id": pt.id,
                "portfolio": pt.portfolio.id,
                "ticker": pt.ticker.ticker,
                "name": pt.ticker.name,
                "currency": pt.currency,
                "logo": request.build_absolute_uri(f"/static/logos/{pt.ticker.ticker}.png")
            })
        return Response(data)

class PortfolioTickerDeleteView(generics.DestroyAPIView):
    serializer_class = PortfolioTickerSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        portfolio_id = self.kwargs["portfolio_id"]
        ticker = self.kwargs["ticker"]
        currency = self.kwargs["currency"].upper()

        return PortfolioTicker.objects.get(
            portfolio__id=portfolio_id,
            portfolio__user=self.request.user,
            ticker__ticker=ticker,
            currency=currency
        )

class PortfolioTickerAvailableView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, portfolio_id):
        portfolio = Portfolio.objects.filter(id=portfolio_id, user=request.user).first()
        if not portfolio:
            return Response({"detail": "Portfolio not found."}, status=404)

        all_currencies = [c[0] for c in PortfolioTicker._meta.get_field("currency").choices]
        existing_tickers = PortfolioTicker.objects.filter(portfolio=portfolio).values_list("ticker__ticker", "currency")
        ticker_currencies = {}
        for ticker, currency in existing_tickers:
            ticker_currencies.setdefault(ticker, set()).add(currency)

        data = []
        for company in Company.objects.all():
            remaining_currencies = set(all_currencies) - ticker_currencies.get(company.ticker, set())
            if remaining_currencies:
                data.append({
                    "ticker": company.ticker,
                    "name": company.name,
                    "currencies": list(remaining_currencies),
                })

        return Response(data)

class PortfolioTickerCurrenciesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, portfolio_id, ticker):
        pt = PortfolioTicker.objects.filter(
            portfolio_id=portfolio_id,
            portfolio__user=request.user,
            ticker__ticker=ticker.upper()
        ).first()

        if not pt:
            return Response({"detail": "Ticker not found."}, status=404)

        company = pt.ticker

        return Response({
            "ticker": pt.ticker.ticker,
            "currencies": [pt.currency],
            "name": company.name
        })

# --------------
# Transaction
# --------------
class PortfolioTransactionListCreateView(generics.ListCreateAPIView):
    """
    GET  -> liste toutes les transactions d'un portefeuille
    POST -> crée une transaction dans un portefeuille
    """
    permission_classes = [IsAuthenticated]
    serializer_class = PortfolioTransactionCreateSerializer

    def get_queryset(self):
        portfolio_id = self.kwargs["portfolio_id"]
        return (
            PortfolioTransaction.objects.filter(
                portfolio_id=portfolio_id,
                portfolio__user=self.request.user,
            )
            .select_related("portfolio_ticker", "portfolio_ticker__ticker")
            .order_by("-date")
        )

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        data = serializer.data

        for item, tx in zip(data, queryset):
            # Conversion des champs numériques en float
            for field in ["amount", "fees", "stock_price", "quantity"]:
                if field in item and item[field] is not None:
                    item[field] = float(item[field])

            # Ajout de l'id de la transaction
            item["id"] = tx.id  

            # Ajout du ticker
            if tx.portfolio_ticker and tx.portfolio_ticker.ticker:
                item["ticker"] = tx.portfolio_ticker.ticker.ticker

            # Conversion du currency en symbole
            currency_code = None
            if tx.portfolio_ticker:
                currency_code = tx.portfolio_ticker.currency
            elif hasattr(tx, "currency") and tx.currency:
                currency_code = tx.currency

            if currency_code in CURRENCY_SYMBOL_MAP:
                item["currency"] = CURRENCY_SYMBOL_MAP[currency_code]

        return Response(data)

    def perform_create(self, serializer):
        data = self.request.data.copy()
        portfolio_id = self.kwargs['portfolio_id']
        portfolio = get_object_or_404(Portfolio, id=portfolio_id, user=self.request.user)

        operation = data.get("operation")
        amount = Decimal(data.get("amount", 0))
        fees = Decimal(data.get("fees", 0))
        currency = data.get("currency")
        date_str = data.get("date")

        # Conversion date
        try:
            date = datetime.fromisoformat(date_str).date() if isinstance(date_str, str) else date_str
        except Exception:
            date = None

        # PortfolioTicker si nécessaire
        portfolio_ticker = None
        if operation in ["buy", "sell", "dividend"]:
            ticker_id = data.get("portfolio_ticker")
            portfolio_ticker = get_object_or_404(
                PortfolioTicker,
                id=ticker_id,
                portfolio=portfolio
            )
            # Calcul quantity
            stock_price = Decimal(data.get("stock_price", 0))
            if stock_price <= 0 and operation in ["buy", "sell"]:
                raise ValueError("Stock price must be > 0 for buy/sell")
            quantity = Decimal(data.get("quantity", 0)) or round(amount / stock_price, 6)
        elif operation in ["interest", "deposit", "withdrawal"]:
            quantity = Decimal(data.get("quantity", 0))
        else:
            return Response({"detail": "Opération non supportée."}, status=status.HTTP_400_BAD_REQUEST)

        # Création transaction
        serializer.save(
            user=self.request.user,
            portfolio=portfolio,
            portfolio_ticker=portfolio_ticker,
            amount=round(amount, 2),
            fees=round(fees, 2),
            quantity=round(quantity, 6) if quantity else None,
            currency=currency,
            date=date
        )

class PortfolioTransactionDetailUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    -> détail d'une transaction
    PUT    -> update complet
    PATCH  -> update partiel
    DELETE -> supprime la transaction
    """
    queryset = PortfolioTransaction.objects.all()
    serializer_class = PortfolioTransactionUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # On ne récupère que les transactions appartenant à l'utilisateur
        return PortfolioTransaction.objects.filter(
            portfolio__user=self.request.user
        )

    def perform_update(self, serializer):
        """
        Logique métier lors de la mise à jour :
        - recalcul de quantity pour buy/sell/dividend
        - vérification de stock_price > 0
        - vérification que le ticker appartient au portefeuille
        """
        data = serializer.validated_data
        operation = data.get('operation', serializer.instance.operation)

        # Recalcul quantity pour certaines opérations
        if operation in ["buy", "sell"]:
            amount = data.get('amount', serializer.instance.amount)
            stock_price = data.get('stock_price', serializer.instance.stock_price)
            if stock_price is None or stock_price == 0:
                raise serializers.ValidationError({"stock_price": "Stock price must be greater than 0."})
            data['quantity'] = round(amount / stock_price, 6)

            # Vérification du ticker
            portfolio_ticker = data.get('portfolio_ticker', serializer.instance.portfolio_ticker)
            if not portfolio_ticker:
                raise serializers.ValidationError({"portfolio_ticker": "Ticker is required for buy/sell."})

        elif operation == "dividend":
            # quantity doit être renseigné
            if 'quantity' not in data:
                data['quantity'] = serializer.instance.quantity or 0

        # Interest, deposit, withdrawal n'ont pas de ticker
        elif operation in ["interest", "deposit", "withdrawal"]:
            data['portfolio_ticker'] = None

        serializer.save()   

class ExcelPortfolioTransactionUploadView(APIView):
    """
    Endpoint RESTful pour importer des transactions via un fichier Excel
    pour un portefeuille donné.
    Crée automatiquement les tickers manquants dans le portefeuille uniquement si la company existe.
    """
    permission_classes = [permissions.IsAuthenticated]

    expected_columns = [
        'Ticker', 'Type', 'Date',
        'Montant', "Prix de l'action lors de la transaction", 'Quantité', 'Frais', 'Devise'
    ]

    def post(self, request, portfolio_id: int):
        file_upload = request.FILES.get("file")
        if not file_upload:
            return html_error_response("Erreur d'import", ["Aucun fichier fourni."])

        # Lecture Excel
        try:
            df = pd.read_excel(BytesIO(file_upload.read()), engine="openpyxl")
            df.columns = df.columns.str.strip()
        except Exception as e:
            return html_error_response("Erreur de lecture du fichier", [str(e)])

        if not all(col in df.columns for col in self.expected_columns):
            return html_error_response(
                "Colonnes Excel incorrectes",
                [
                    f"Colonnes attendues : {', '.join(self.expected_columns)}",
                    f"Colonnes reçues : {', '.join(df.columns)}"
                ]
            )

        df = self._clean_dataframe(df)

        # Création automatique des tickers manquants si Company existe
        missing_tickers_error = self._create_missing_tickers(df, portfolio_id, request.user)
        if missing_tickers_error:
            return html_error_response("Tickers manquants", missing_tickers_error)

        to_create, to_update = self._prepare_transactions(df, portfolio_id, request)

        with transaction.atomic():
            for serializer in to_create:
                serializer.save()
            for instance, new_amount, new_fees, new_quantity in to_update:
                instance.amount = new_amount
                instance.fees = new_fees
                instance.quantity = new_quantity
                instance.save()

        return Response({"importées": len(to_create) + len(to_update)}, status=status.HTTP_201_CREATED)

    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        df['Ticker'] = df['Ticker'].fillna('')
        df['Devise'] = df['Devise'].fillna('')
        df['Date'] = pd.to_datetime(df['Date']).dt.date
        grouped = df.groupby(
            ['Ticker', 'Type', 'Date', 'Devise', "Prix de l'action lors de la transaction"],
            as_index=False
        ).agg({'Montant': 'sum', 'Quantité': 'sum', 'Frais': 'sum'})
        return grouped

    def _create_missing_tickers(self, df: pd.DataFrame, portfolio_id: int, user) -> list:
        """
        Crée les tickers manquants pour le portefeuille uniquement si la company existe.
        Retourne une liste d'erreurs pour les tickers dont la company n'existe pas.
        """
        errors = []
        tickers_in_excel = {(t, c) for t, c in zip(df['Ticker'], df['Devise']) if t.strip()}
        existing_tickers = set(
            PortfolioTicker.objects.filter(
                portfolio_id=portfolio_id, portfolio__user=user
            ).values_list("ticker__ticker", "currency")
        )

        missing_tickers = tickers_in_excel - existing_tickers

        for ticker_symbol, currency in missing_tickers:
            company = Company.objects.filter(ticker=ticker_symbol).first()
            if not company:
                errors.append(f"Le ticker '{ticker_symbol}' n'existe pas dans la table Company.")
                continue
            PortfolioTicker.objects.create(
                portfolio_id=portfolio_id,
                ticker=company,
                currency=currency
            )

        return errors

    def _prepare_transactions(self, df: pd.DataFrame, portfolio_id: int, request) -> tuple[list, list]:
        to_create, to_update = [], []

        for index, row in df.iterrows():
            operation = row['Type']
            tx_date = row['Date']
            ticker = row['Ticker']
            currency = row.get('Devise')

            try:
                amount = Decimal(abs(float(row['Montant'])))
                fees = Decimal(abs(float(row['Frais'])))
                stock_price = Decimal(float(row["Prix de l'action lors de la transaction"]))
                quantity = Decimal(abs(float(row['Quantité'])))
            except Exception as e:
                raise ValidationError({f"Ligne {index + 2}": f"Problème de conversion numérique : {e}"})

            # Récupération du PortfolioTicker si nécessaire
            portfolio_ticker_obj = None
            if operation in ["buy", "sell", "dividend"]:
                portfolio_ticker_obj = PortfolioTicker.objects.filter(
                    portfolio_id=portfolio_id,
                    ticker__ticker=ticker,
                    currency=currency
                ).first()
                if not portfolio_ticker_obj:
                    raise ValidationError({f"Ligne {index + 2}": f"Le ticker '{ticker}' n'existe pas dans le portefeuille."})
            # interest, deposit, withdrawal → pas de ticker, on ignore

            # Calcul quantity si achat/vente
            if operation in ["buy", "sell"]:
                if stock_price == 0:
                    raise ValidationError({f"Ligne {index + 2}": "Division par zéro : prix de l'action = 0"})
                quantity = round((amount + fees) / stock_price, 6) if operation == "sell" else round(amount / stock_price, 6)

            # Vérifie si transaction existe déjà
            existing_tx = None
            if operation in ["buy", "sell", "dividend"]:
                existing_tx = PortfolioTransaction.objects.filter(
                    portfolio=portfolio_id,
                    portfolio_ticker=portfolio_ticker_obj,
                    date=tx_date,
                    stock_price=stock_price,
                    operation=operation,
                    currency=currency
                ).first()

            if existing_tx:
                new_quantity = round((existing_tx.amount + amount) / stock_price, 6) if operation in ["buy", "sell"] else quantity
                to_update.append((existing_tx, existing_tx.amount + amount, existing_tx.fees + fees, new_quantity))
            else:
                serializer_data = {
                    "portfolio": portfolio_id,
                    "operation": operation,
                    "date": tx_date,
                    "amount": round(float(amount), 2),
                    "fees": round(float(fees), 2),
                    "quantity": round(float(quantity), 6),
                    "stock_price": round(float(stock_price), 2) if operation in ["buy", "sell"] else None,
                    "portfolio_ticker": portfolio_ticker_obj.pk if portfolio_ticker_obj else None,
                    "currency": currency,
                }
                serializer = PortfolioTransactionCreateSerializer(data=serializer_data, context={'request': request})
                serializer.is_valid(raise_exception=True)
                to_create.append(serializer)

        return to_create, to_update
    

# --------------
# Portefeuille Performance
# --------------
class UserPortfolios(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        portfolios = Portfolio.objects.filter(user=request.user).values("id", "name")
        return Response([{"id": p["id"], "name": p["name"]} for p in portfolios])

class UserPortfolioPerformanceSummary(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        portfolios = Portfolio.objects.filter(user=request.user).exclude(name="all").values("id", "name")
        return Response([{"id": p["id"], "name": p["name"]} for p in portfolios])

class PortfolioPerformanceDynamicView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, portfolio_id: int):
        requested_fields = request.query_params.get("fields")
        if not requested_fields:
            return Response({"error": "Missing `fields` parameter."}, status=status.HTTP_400_BAD_REQUEST)

        field_list = [f.strip() for f in requested_fields.split(",")]
        data = get_portfolio_performance_data(request.user, portfolio_id, field_list)
        if data is None:
            return Response({"error": "PortfolioPerformance not found."}, status=status.HTTP_404_NOT_FOUND)

        return Response(data, status=status.HTTP_200_OK)

class UserPortfolioPerformanceRepartitionAllPortfolio(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        portfolios = Portfolio.objects.filter(user=user).exclude(name="all").values_list('name', 'id')
        color_palette = [
            "#5863f8", "#c70039", "#5dd39e", "#fdfd96", "#6c5ce7",
            "#9467bd", "#00cec9", "#fa824c", "#00b894", "#ff7675",
            "#ffa630", "#fd79a8", "#e17055", "#fab1a0", "#55efc4"
        ]

        chart_config = {"repartition": {"label": "Répartition"}}
        portfolios_valuation = []

        for idx, (portfolio_name, portfolio_id) in enumerate(portfolios):
            data = get_portfolio_performance_data(user, portfolio_id, ["portfolio_valuation"])
            last_value = 0
            if data and data.get("portfolio_valuation"):
                last_entry = data["portfolio_valuation"][-1]
                last_value = last_entry.get(portfolio_name, 0)
            color = color_palette[idx % len(color_palette)]
            portfolios_valuation.append({"portfolio": portfolio_name, "repartition": last_value, "fill": color})
            chart_config[portfolio_name] = {"label": portfolio_name, "color": color}

        total_valuation = sum(p["repartition"] for p in portfolios_valuation)
        portfolios_repartition = [
            {
                "portfolio": p["portfolio"],
                "repartition": round((p["repartition"] / total_valuation * 100) if total_valuation > 0 else 0, 2),
                "fill": p["fill"]
            }
            for p in portfolios_valuation
        ]
        return Response((portfolios_repartition, chart_config), status=status.HTTP_200_OK)

class UserPortfolioPerformanceTwrDate(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, start_date: str, portfolio_id: int):
        tickers_valuations = request.data.get("tickers_valuations")
        if not isinstance(tickers_valuations, dict):
            return Response({"error": "tickers_valuations must be a dictionary"}, status=400)

        start_date_pd = pd.to_datetime(start_date)
        portefeuille = PortfolioPerformances(
            user=request.user,
            portfolios=portfolio_id,
            start_date=start_date_pd,
            tickers_valuations=tickers_valuations
        )
        return Response(portefeuille.get_twr())

class PortfolioPositionSummaryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, portfolio_id: int):
        portfolio = get_object_or_404(Portfolio, id=portfolio_id, user=request.user)
        tickers = PortfolioTicker.objects.filter(portfolio=portfolio)
        result = []

        for pt in tickers:
            perf = TickerPerformanceCompareSP500.objects.filter(
                user=request.user, portfolio=portfolio, ticker=pt
            ).order_by("-last_calculated_at").first()
            if not perf:
                continue
            company = pt.ticker
            logo_url = request.build_absolute_uri(f"/static/logos/{company.ticker}.png")
            currency = CURRENCY_SYMBOL_MAP.get(perf.currency, perf.currency)
            result.append({
                "ticker": company.ticker,
                "name": company.name,
                "nbBuy": float(perf.number_of_transactions),
                "logo": logo_url,
                "amountInvest": float(perf.purchase_amount),
                "value": float(perf.current_value),
                "gains": float(perf.total_gain),
                "gainsPercentage": float(perf.gain_percentage),
                "gainsSP500": float(perf.sp500_value),
                "gainsPercentageSP500": float(perf.sp500_gain_percentage),
                "difference": float(perf.performance_gap),
                "durationDay": float(perf.holding_duration),
                "annualizedPercentage": float(perf.annualized_return),
                "capitalGainOrLoss": float(perf.total_gain),
                "capitalGainOrLossPercentage": float(perf.gain_percentage),
                "dividendAmount": float(perf.dividend_amount),
                "dividendYieldPercentage": float(perf.dividend_yield),
                "quantity": float(perf.quantity),
                "fees": float(perf.transaction_fees),
                "currency": currency,
            })
        return Response(sorted(result, key=lambda x: x["value"], reverse=True))

class PortfolioTransactionCompareDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, portfolio_id: int, ticker: str):
        portfolio = get_object_or_404(Portfolio, id=portfolio_id, user=request.user)
        portfolio_ticker = get_object_or_404(PortfolioTicker, portfolio=portfolio, ticker__ticker=ticker)
        transactions = TransactionCompareSP500.objects.filter(user=request.user, portfolio=portfolio, ticker=portfolio_ticker).order_by("date")
        if not transactions.exists():
            return Response({"error": "No transactions found for this ticker."}, status=404)
        logo_url = request.build_absolute_uri(f"/static/logos/{ticker}.png")
        result = [
            {
                "id": idx+1,
                "ticker": portfolio_ticker.ticker.ticker,
                "logo": logo_url,
                "dateBuy": tx.date,
                "amount": float(tx.purchase_amount),
                "stockValue": float(tx.current_value),
                "gains": float(tx.total_gain),
                "gainsPercentage": float(tx.gain_percentage),
                "gainsSP500": float(tx.sp500_value),
                "gainsPercentageSP500": float(tx.sp500_gain_percentage),
                "difference": float(tx.performance_gap),
                "durationDay": float(tx.holding_duration),
                "annualizedPercentage": float(tx.annualized_return),
                "capitalGainOrLoss": float(tx.total_gain),
                "capitalGainOrLossPercentage": float(tx.gain_percentage),
                "dividendAmount": float(tx.dividend_amount),
                "dividendYieldPercentage": float(tx.dividend_yield),
                "quantity": float(tx.quantity),
                "pru": float(tx.stock_price),
                "fees": float(tx.transaction_fees),
            } for idx, tx in enumerate(transactions)
        ]
        return Response(sorted(result, key=lambda x: x["dateBuy"], reverse=True))

class PortfolioAllTransactionsCompareDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, portfolio_id: int):
        portfolio = get_object_or_404(Portfolio, id=portfolio_id, user=request.user)
        portfolio_tickers = PortfolioTicker.objects.filter(portfolio=portfolio)
        result = []
        for ticker_obj in portfolio_tickers:
            ticker = ticker_obj.ticker.ticker
            logo_url = request.build_absolute_uri(f"/static/logos/{ticker}.png")
            transactions = TransactionCompareSP500.objects.filter(user=request.user, portfolio=portfolio, ticker=ticker_obj).order_by("date")
            result.extend([
                {
                    "ticker": ticker,
                    "logo": logo_url,
                    "dateBuy": tx.date,
                    "amount": float(tx.purchase_amount),
                    "stockValue": float(tx.current_value),
                    "gains": float(tx.total_gain),
                    "gainsPercentage": float(tx.gain_percentage),
                    "gainsSP500": float(tx.sp500_value),
                    "gainsPercentageSP500": float(tx.sp500_gain_percentage),
                    "difference": float(tx.performance_gap),
                    "durationDay": float(tx.holding_duration),
                    "annualizedPercentage": float(tx.annualized_return),
                    "capitalGainOrLoss": float(tx.total_gain),
                    "capitalGainOrLossPercentage": float(tx.gain_percentage),
                    "dividendAmount": float(tx.dividend_amount),
                    "dividendYieldPercentage": float(tx.dividend_yield),
                    "quantity": float(tx.quantity),
                    "pru": float(tx.stock_price),
                    "fees": float(tx.transaction_fees),
                }
                for tx in transactions
            ])
        # Tri par date décroissante et id
        result_sorted = sorted(result, key=lambda x: x["dateBuy"], reverse=True)
        for idx, tx in enumerate(result_sorted, start=1):
            tx["id"] = idx
        return Response(result_sorted)

class PortfolioTickerPerformanceView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, portfolio_id: int):
        user = request.user
        latest_perfs = TickerPerformanceCompareSP500.objects.filter(
            portfolio__user=user, portfolio__id=portfolio_id
        ).values('ticker').annotate(latest_id=Max('id'))
        performances = TickerPerformanceCompareSP500.objects.filter(
            id__in=[item['latest_id'] for item in latest_perfs]
        )
        result = {key: [] for key in ["Montant", "%", "% / an", "sp500"]}
        for perf in performances:
            if not perf.ticker:
                continue
            company = perf.ticker.ticker
            logo_url = request.build_absolute_uri(f"/static/logos/{company.ticker}.png")
            amount_value = float(perf.total_gain)
            if perf.currency != "EUR":
                amount_value = StockPrice.convert_price(amount_value, from_currency=perf.currency, to_currency="EUR", date=perf.last_calculated_at)
            entry_base = {"companyName": company.name, "ticker": company.ticker, "logoUrl": logo_url}
            result["Montant"].append({**entry_base, "value": amount_value})
            result["%"].append({**entry_base, "value": float(perf.gain_percentage)})
            result["% / an"].append({**entry_base, "value": float(perf.annualized_return)})
            result["sp500"].append({**entry_base, "value": float(perf.performance_gap)})
        # Tri décroissant sur value
        for key in result:
            result[key] = sorted(result[key], key=lambda x: x["value"], reverse=True)
        return Response(result)



class CurrencyListView(APIView):
    """
    Retourne toutes les devises disponibles.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        currencies = [{"code": code, "label": label} for code, label in CURRENCY_CHOICES]
        return Response(currencies, status=200)

class CurrencyTickerView(APIView):
    """
    Retourne un dictionnaire {ticker: currency} pour un portefeuille donné.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        portfolio_id = request.GET.get("portfolio_id")
        if not portfolio_id:
            return Response({"error": "portfolio_id est requis."}, status=400)

        tickers = PortfolioTicker.objects.filter(portfolio_id=portfolio_id)

        # Dictionnaire {code: symbole} à partir des choices
        currency_map = dict(CURRENCY_CHOICES)

        # On renvoie le symbole à la place du code
        ticker_currency_map = {
            ticker.ticker.ticker: currency_map.get(ticker.currency, ticker.currency)
            for ticker in tickers
        }

        return Response(ticker_currency_map)



def get_portfolio_performance_data(user, portfolio_id, fields: list[str]):
    try:
        performance = PortfolioPerformance.objects.get(user=user, portfolio_id=portfolio_id)
    except PortfolioPerformance.DoesNotExist:
        return None

    valid_fields = {
        field.name for field in PortfolioPerformance._meta.fields
        if field.name not in ["id", "user", "portfolio", "last_calculated_at"]
    }

    data = {}
    for field in fields:
        clean_field = field.strip()
        if clean_field in valid_fields:
            data[clean_field] = getattr(performance, clean_field)
        else:
            data[clean_field] = None  # ou logguer un avertissement
    return data
