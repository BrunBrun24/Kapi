import calendar
from datetime import date, datetime
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
from django.db.models.functions import ExtractYear, ExtractMonth
from django.db.models import Max, Sum, F
from rest_framework import serializers

from api.utils import html_error_response
from api.services.modules.portfolio_performances import PortfolioPerformances

from .models import (
    CURRENCY_CHOICES,
    PORTFOLIO_MAIN_NAME,
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


class PortfolioDividendsMonthView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, portfolio_id: int):
        data = get_portfolio_performance_data(request.user, portfolio_id, ["portfolio_dividends"])

        # Récupération brute
        portfolio_dividends_raw = data.get("portfolio_dividends", [])
        if not portfolio_dividends_raw:
            return Response({})

        # DataFrame propre
        portfolio_dividends = pd.DataFrame(portfolio_dividends_raw)
        portfolio_dividends = portfolio_dividends.drop_duplicates(subset=["date", "all"])
        portfolio_dividends["date"] = pd.to_datetime(portfolio_dividends["date"])
        portfolio_dividends.set_index("date", inplace=True)

        # Colonnes année/mois
        portfolio_dividends["month"] = portfolio_dividends.index.month
        portfolio_dividends["year"] = portfolio_dividends.index.year

        # Liste des années
        years = sorted(portfolio_dividends["year"].unique().astype(int))

        # Dictionnaire {année: {mois: total}}
        year_month_dict = {}
        for year in years:
            df_year = portfolio_dividends[portfolio_dividends["year"] == year]
            month_totals = df_year.groupby("month")["all"].sum().round(2).to_dict()

            # Conversion explicite des clés numpy en int
            month_totals = {int(month): float(total) for month, total in month_totals.items()}
            year_month_dict[int(year)] = month_totals

        return Response(year_month_dict)

class PortfolioDividendsByTickerMonthView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, portfolio_id):
        # Récupérer toutes les transactions dividendes pour ce portefeuille et cet utilisateur
        transactions = PortfolioTransaction.objects.filter(
            portfolio_ticker__portfolio__id=portfolio_id,
            portfolio_ticker__portfolio__user_id=request.user.id,
            operation="dividend"
        ).select_related("portfolio_ticker__ticker")

        if not transactions.exists():
            return Response([])

        # Créer un DataFrame
        df = pd.DataFrame.from_records(
            transactions.values(
                "date",
                "amount",
                "fees",
                "portfolio_ticker__ticker__ticker",
                "portfolio_ticker__ticker__name"
            )
        )

        # Calculer les dividendes nets
        df["net_amount"] = df["amount"] - df["fees"].fillna(0)

        # Conversion en datetime
        df["date"] = pd.to_datetime(df["date"])

        # Renommer colonnes
        df.rename(
            columns={
                "portfolio_ticker__ticker__ticker": "ticker",
                "portfolio_ticker__ticker__name": "company_name"
            },
            inplace=True
        )

        # Extraire année et mois
        df["year"] = df["date"].dt.year
        df["month"] = df["date"].dt.month
        df["month_name"] = df["month"].apply(lambda m: calendar.month_abbr[m])

        # Grouper par année, mois et ticker
        monthly_data = df.groupby(["year", "month_name", "ticker"])["net_amount"].sum().reset_index()

        month_order = list(calendar.month_abbr)[1:]  # ["Jan", ..., "Dec"]

        # Pivot pour avoir une colonne par ticker
        pivot = monthly_data.pivot_table(
            index=["year", "month_name"],
            columns="ticker",
            values="net_amount",
            fill_value=0
        ).reset_index()

        # Récupérer première et dernière date de transaction du portefeuille
        first_date, last_date = PortfolioTransaction.first_and_last_date(
            user=request.user,
            portfolio=portfolio_id
        )
        if not first_date or not last_date:
            return Response([])

        # Construire le format final avec tous les mois depuis la première transaction
        result = []

        for year in sorted(pivot["year"].unique()):
            year_data = pivot[pivot["year"] == year].copy()

            # Définir les bornes pour l'année
            year_start = first_date if first_date.year == year else pd.Timestamp(year=year, month=1, day=1)
            year_end = last_date if last_date.year == year else pd.Timestamp(year=year, month=12, day=31)
            months_in_year = pd.period_range(start=year_start, end=year_end, freq="M").strftime("%b")

            # Ajouter les mois manquants avec 0 pour tous les tickers
            for m in months_in_year:
                if m not in year_data["month_name"].values:
                    empty_row = {"year": year, "month_name": m}
                    for ticker in pivot.columns:
                        if ticker not in ["year", "month_name"]:
                            empty_row[ticker] = 0
                    year_data = pd.concat([year_data, pd.DataFrame([empty_row])], ignore_index=True)

            # Trier par ordre des mois
            year_data["month_index"] = year_data["month_name"].apply(lambda m: month_order.index(m))
            year_data.sort_values("month_index", inplace=True)

            # Construire la structure finale
            for _, row in year_data.iterrows():
                data_entry = {"month": row["month_name"]}
                for ticker in row.index:
                    if ticker in ["year", "month_name", "month_index"]:
                        continue
                    if row[ticker] > 0:
                        data_entry[ticker] = row[ticker]
                result.append({"year": year, "data": data_entry})

        # Trier les tickers dans chaque mois par montant décroissant
        for entry in result:
            data = entry["data"]
            month_value = data.pop("month")
            sorted_tickers = dict(sorted(data.items(), key=lambda item: item[1], reverse=True))
            entry["data"] = {"month": month_value, **sorted_tickers}

        return Response(result)

class PortfolioDividendsYearView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, portfolio_id: int):
        data = get_portfolio_performance_data(request.user, portfolio_id, ["portfolio_dividends"])

        # Récupération brute
        portfolio_dividends_raw = data.get("portfolio_dividends", [])
        if not portfolio_dividends_raw:
            return Response({})

        # Conversion en DataFrame
        portfolio_dividends = pd.DataFrame(portfolio_dividends_raw)
        portfolio_dividends = portfolio_dividends.drop_duplicates(subset=["date", "all"])
        portfolio_dividends["date"] = pd.to_datetime(portfolio_dividends["date"])
        portfolio_dividends.set_index("date", inplace=True)

        # Extraire l'année
        portfolio_dividends["year"] = portfolio_dividends.index.year

        # Somme totale des dividendes par année
        year_totals = portfolio_dividends.groupby("year")["all"].sum().round(2).to_dict()

        # Conversion explicite des clés numpy → int, valeurs → float
        year_totals = {int(year): float(total) for year, total in year_totals.items()}

        return Response(year_totals)

class PortfolioDividendsByTickerYearView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, portfolio_id):
        # Récupérer toutes les transactions dividendes pour ce portefeuille et cet utilisateur
        transactions = PortfolioTransaction.objects.filter(
            portfolio_ticker__portfolio__id=portfolio_id,
            portfolio_ticker__portfolio__user_id=request.user.id,
            operation="dividend"
        ).select_related("portfolio_ticker__ticker")

        if not transactions.exists():
            return Response([])

        # Créer un DataFrame à partir des transactions
        df = pd.DataFrame.from_records(
            transactions.values(
                "date",
                "amount",
                "fees",
                "portfolio_ticker__ticker__ticker",
                "portfolio_ticker__ticker__name"
            )
        )

        # Dividendes nets
        df["net_amount"] = df["amount"] - df["fees"].fillna(0)

        # Conversion date
        df["date"] = pd.to_datetime(df["date"])

        # Renommer les colonnes
        df.rename(
            columns={
                "portfolio_ticker__ticker__ticker": "ticker",
                "portfolio_ticker__ticker__name": "company_name"
            },
            inplace=True
        )

        # Extraire l’année
        df["month"] = df["date"].dt.year

        # Grouper par année et ticker
        yearly_data = (
            df.groupby(["month", "ticker"])["net_amount"]
            .sum()
            .reset_index()
        )

        # Pivot : 1 ligne par année, colonnes = tickers
        pivot = yearly_data.pivot_table(
            index="month",
            columns="ticker",
            values="net_amount",
            fill_value=0
        ).reset_index()

        # Conversion en liste de dictionnaires
        result = pivot.to_dict(orient="records")

        # Supprimer les tickers avec valeur 0 pour chaque année
        for item in result:
            keys_to_remove = [key for key, value in item.items() if key != "month" and value == 0]
            for key in keys_to_remove:
                del item[key]

        # Convertir l'année en string
        for item in result:
            item["month"] = str(item["month"])

        return Response(result)

class PortfolioDividendsYearsListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, portfolio_id: int):
        data = get_portfolio_performance_data(
            request.user, portfolio_id, ["portfolio_dividends"]
        )

        portfolio_dividends_raw = data.get('portfolio_dividends', [])

        if not portfolio_dividends_raw:
            # Si aucun dividende, retourner une liste vide
            return Response([])

        # Transformation en DataFrame
        portfolio_dividends = pd.DataFrame(portfolio_dividends_raw)

        if portfolio_dividends.empty or 'date' not in portfolio_dividends.columns:
            return Response([])

        portfolio_dividends['date'] = pd.to_datetime(portfolio_dividends['date'])
        portfolio_dividends.set_index('date', inplace=True)

        portfolio_dividends['month'] = portfolio_dividends.index.month
        portfolio_dividends['year'] = portfolio_dividends.index.year

        years = sorted(portfolio_dividends['year'].unique().astype(int))

        print(years)
        return Response(years)


class PortfolioDepositsMonthView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, portfolio_id):
        # On récupère les dépôts
        deposits = (
            PortfolioTransaction.objects.filter(
                user=request.user,
                portfolio=portfolio_id,
                operation="deposit",
            )
            .annotate(year=ExtractYear("date"), month=ExtractMonth("date"))
            .values("year", "month")
            .annotate(total_amount=Sum(F("amount") - F("fees")))
            .order_by("year", "month")
        )

        # Construction du dictionnaire {année: {mois: montant}}
        result = {}
        for entry in deposits:
            year = entry["year"]
            month = entry["month"]
            total = float(entry["total_amount"] or 0)
            result.setdefault(year, {})[month] = total

        if not result:
            return Response({})  # Aucun dépôt

        # Détermination des bornes temporelles
        years = sorted(result.keys())
        min_year, max_year = years[0], years[-1]

        # Premier et dernier mois réels trouvés
        first_month = min(result[min_year].keys())
        # Si dernière année est l'année en cours, on s'arrête au mois actuel
        current_year, current_month = date.today().year, date.today().month
        if max_year == current_year:
            last_month = current_month
        else:
            last_month = max(result[max_year].keys())

        # Remplissage des mois manquants
        for year in range(min_year, max_year + 1):
            if year == min_year and year == max_year:
                # Une seule année de données
                start, end = first_month, last_month
            elif year == min_year:
                start, end = first_month, 12
            elif year == max_year:
                start, end = 1, last_month
            else:
                start, end = 1, 12

            if year not in result:
                result[year] = {}

            for month in range(start, end + 1):
                result[year].setdefault(month, 0.0)

        # Tri des clés pour un rendu propre
        result = {y: dict(sorted(m.items())) for y, m in sorted(result.items())}

        return Response(result)

class PortfolioDepositsByNameMonthView(APIView):
    """
    Vue RESTful pour agréger les dépôts d'argent par année, mois et portefeuille.
    Retourne une structure similaire à PortfolioDividendsMonthView,
    mais avec les noms de portefeuilles au lieu des tickers.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, portfolio_id):
        # On sélectionne uniquement les opérations de type "deposit"
        deposits = (
            PortfolioTransaction.objects.filter(
                user=request.user,
                portfolio=portfolio_id,
                operation="deposit",
            )
            .annotate(year=ExtractYear("date"), month=ExtractMonth("date"))
            .values("year", "month", "portfolio__name", "currency")
            .annotate(total_amount=Sum(F("amount") - F("fees")))
            .order_by("year", "month")
        )

        # Structure cible : [{'year': 2023, 'data': {'month': 'Jan', 'Portefeuille A': 100.0, ...}}, ...]
        result = []
        current_year = None
        current_month_data = {}

        for entry in deposits:
            year = int(entry["year"])
            month = int(entry["month"])
            portfolio_name = entry["portfolio__name"]
            amount = float(entry["total_amount"] or 0)

            # Si changement d'année ou nouveau mois
            if current_year != year:
                current_year = year
                current_month_data = {"year": year, "data": {"month": self._get_month_name(month)}}
                result.append(current_month_data)
            elif result and result[-1]["data"]["month"] != self._get_month_name(month):
                current_month_data = {"year": year, "data": {"month": self._get_month_name(month)}}
                result.append(current_month_data)

            # Ajout du montant pour le portefeuille correspondant
            current_month_data["data"][portfolio_name] = amount

        return Response(result)

    def _get_month_name(self, month_number: int) -> str:
        """Renvoie le nom abrégé du mois à partir de son numéro."""
        import calendar
        return calendar.month_abbr[month_number]
        
class PortfolioDepositYearView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, portfolio_id):
        # Filtrer les dépôts de l'utilisateur pour le portefeuille spécifié
        deposits = (
            PortfolioTransaction.objects
            .filter(
                user=request.user,
                portfolio=portfolio_id,
                operation='deposit'
            )
            .annotate(year=ExtractYear('date'))
            .values('year')
            .annotate(total_amount=Sum(F("amount") - F("fees")))
            .order_by('year')
        )

        # Construire le dictionnaire {année: total}
        result = {str(entry['year']): round(entry['total_amount'], 2) for entry in deposits if entry['year']}

        return Response(result)

class PortfolioDepositsByPortfolioYearView(APIView):
    """
    Vue RESTful pour récupérer les dépôts annuels détaillés par portefeuille.
    Retourne une liste de dicts avec 'month' = année et clés = noms de portefeuilles.
    Les frais sont déduits des montants.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, portfolio_id):
        # Récupérer les transactions de type "deposit" pour cet utilisateur
        deposits = PortfolioTransaction.objects.filter(
            user=request.user,
            portfolio=portfolio_id,
            operation="deposit"
        ).select_related("portfolio")

        if not deposits.exists():
            return Response([])

        # Construire DataFrame
        df = pd.DataFrame.from_records(
            deposits.values(
                "date",
                "amount",
                "fees",
                "portfolio__name"
            )
        )

        # Déduire les frais
        df["net_amount"] = df["amount"] - df["fees"]

        df["date"] = pd.to_datetime(df["date"])
        df["year"] = df["date"].dt.year

        # Grouper par année et portefeuille
        yearly_data = df.groupby(["year", "portfolio__name"])["net_amount"].sum().reset_index()

        # Pivot pour avoir 1 ligne par année, colonnes = noms de portefeuilles
        pivot = yearly_data.pivot_table(
            index="year",
            columns="portfolio__name",
            values="net_amount",
            fill_value=0
        ).reset_index()

        # Conversion en liste de dicts
        result = pivot.to_dict(orient="records")

        # Supprimer les portefeuilles avec montant 0 pour chaque année
        for item in result:
            keys_to_remove = [key for key, value in item.items() if key != "year" and value == 0]
            for key in keys_to_remove:
                del item[key]

        # Renommer 'year' en 'month' pour garder la même structure que DividendsYearView
        for item in result:
            item["month"] = str(item.pop("year"))

        return Response(result)

class PortfolioDepositYearsListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, portfolio_id: int):
        data = get_portfolio_performance_data(
            request.user, portfolio_id, ["portfolio_dividends"]
        )

        portfolio_dividends_raw = data.get('portfolio_dividends', [])

        if not portfolio_dividends_raw:
            # Si aucun dividende, retourner une liste vide
            return Response([])

        # Transformation en DataFrame
        portfolio_dividends = pd.DataFrame(portfolio_dividends_raw)

        if portfolio_dividends.empty or 'date' not in portfolio_dividends.columns:
            return Response([])

        portfolio_dividends['date'] = pd.to_datetime(portfolio_dividends['date'])
        portfolio_dividends.set_index('date', inplace=True)

        portfolio_dividends['month'] = portfolio_dividends.index.month
        portfolio_dividends['year'] = portfolio_dividends.index.year

        years = sorted(portfolio_dividends['year'].unique().astype(int))

        return Response(years)



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
