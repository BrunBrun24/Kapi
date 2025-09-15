from datetime import datetime
from decimal import Decimal, InvalidOperation
from io import BytesIO
from django.shortcuts import get_object_or_404
import pandas as pd
from rest_framework import generics, permissions, status
from rest_framework.generics import UpdateAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Max

from api.utils import html_error_response
from api.services.modules.portfolio_performances import PorfolioPerformances

from .models import (
    CURRENCY_CHOICES,
    Company,
    PortfolioPerformance,
    StockPrice,
    TickerPerformanceCompareSP500,
    TransactionCompareSP500,
    UserPreference,
    Portfolio,
    PortfolioTicker,
    PortfolioTransaction
)

from .serializers import (
    PortfolioTickerSerializer,
    PortfolioSerializer,
    PortfolioTransactionCreateSerializer,
    PortfolioTransactionDetailSerializer,
    PortfolioTransactionUpdateSerializer,
    UserSerializer
)

User = get_user_model()


# Utilisateur
class CreateUserView(generics.CreateAPIView):
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


# Portefeuille
class UserPortfoliosView(APIView):
    """
    Récupère tous les portefeuilles appartenant à l'utilisateur connecté.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        portfolios = Portfolio.get_user_portfolios(request.user)
        serializer = PortfolioSerializer(portfolios, many=True)
        return Response(serializer.data)

class CreatePortfolioView(generics.CreateAPIView):
    """
    Permet à un utilisateur authentifié de créer un nouveau portefeuille.
    """
    queryset = Portfolio.objects.all()
    serializer_class = PortfolioSerializer
    permission_classes = [IsAuthenticated]

class DeletePortfolioView(APIView):
    """
    Supprime un portefeuille appartenant à l'utilisateur connecté.
    """
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, portfolio_id, *args, **kwargs):
        try:
            portfolio = Portfolio.objects.get(id=portfolio_id, user=request.user)
        except Portfolio.DoesNotExist:
            return Response({"detail": "Portfolio not found."}, status=status.HTTP_404_NOT_FOUND)

        portfolio.delete()
        return Response({"detail": "Portfolio deleted successfully."}, status=status.HTTP_204_NO_CONTENT)

class UpdatePortfolioView(UpdateAPIView):
    """
    Permettre à un utilisateur authentifié de modifier un portefeuille
    (par exemple, son nom ou sa date de création, si autorisé)
    """
    serializer_class = PortfolioSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Limite aux portefeuilles de l'utilisateur connecté
        return Portfolio.objects.filter(user=self.request.user)


# Portefeuille Ticker
class AddPortfolioTickerView(generics.CreateAPIView):
    """
    Permet à un utilisateur authentifié d'ajouter un ticker à un portefeuille.
    """
    queryset = PortfolioTicker.objects.all()
    serializer_class = PortfolioTickerSerializer
    permission_classes = [IsAuthenticated]

class PortfolioTickersView(APIView):
    """
    Récupère tous les tickers d'un portefeuille
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        portfolio_id = kwargs.get("portfolio_id")
        if not portfolio_id:
            return Response({"error": "Portfolio ID manquant."}, status=400)

        tickers = PortfolioTicker.objects.filter(portfolio_id=portfolio_id)
        data = [
            {
                "ticker": pt.ticker.ticker,
                "name": pt.ticker.name,
                "currency": pt.currency,
                "logo": request.build_absolute_uri(f"/static/logos/{pt.ticker.ticker}.png")
            }
            for pt in tickers
        ]
        return Response(data, status=200)

class PortfolioAvailableTickersView(APIView):
    """
    Retourne tous les tickers qui ne sont pas encore associés à un portefeuille donné
    pour une devise donnée. Si un ticker est déjà présent dans toutes les devises possibles,
    il n'est pas ajouté.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, portfolio_id, *args, **kwargs):
        # Vérifier que le portefeuille appartient bien à l'utilisateur
        try:
            portfolio = Portfolio.objects.get(id=portfolio_id, user=request.user)
        except Portfolio.DoesNotExist:
            return Response({"detail": "Portfolio not found."}, status=404)

        # Récupérer toutes les devises disponibles pour PortfolioTicker
        all_currencies = [c[0] for c in PortfolioTicker._meta.get_field("currency").choices]

        # Récupérer les tickers déjà présents dans le portefeuille avec leur devise
        existing_tickers = PortfolioTicker.objects.filter(portfolio=portfolio).values_list("ticker__ticker", "currency")

        # Transformer en dict { "AAPL": {"USD", "EUR"} }
        ticker_currencies = {}
        for ticker, currency in existing_tickers:
            ticker_currencies.setdefault(ticker, set()).add(currency)

        # Tous les tickers possibles
        available_companies = Company.objects.all()

        data = []
        for company in available_companies:
            existing_for_company = ticker_currencies.get(company.ticker, set())
            remaining_currencies = set(all_currencies) - existing_for_company

            # S'il reste au moins une devise possible, on ajoute l'action
            if remaining_currencies:
                data.append({
                    "ticker": company.ticker,
                    "name": company.name,
                    "currencies": list(remaining_currencies)
                })

        return Response(data)

class DeletePortfolioTickerView(APIView):
    """
    Supprime un ticker+currency d'un portefeuille appartenant à l'utilisateur connecté.
    """
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, portfolio_id, ticker, currency, *args, **kwargs):
        try:
            portfolio_ticker = PortfolioTicker.objects.get(
                portfolio__id=portfolio_id,
                portfolio__user=request.user,
                ticker__ticker=ticker,
                currency=currency.upper()  # On sécurise
            )
        except PortfolioTicker.DoesNotExist:
            return Response(
                {"detail": "PortfolioTicker not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        portfolio_ticker.delete()
        return Response(
            {"detail": f"PortfolioTicker {ticker}/{currency} deleted successfully."},
            status=status.HTTP_204_NO_CONTENT
        )

class PortfolioTickerCurrenciesView(APIView):
    """
    Retourne les devises disponibles pour un ticker donné
    dans un portefeuille précis d'un utilisateur.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, portfolio_id: int, ticker: str):
        try:
            currencies = PortfolioTicker.get_currencies_for_ticker(
                user_id=request.user.id,
                portfolio_id=portfolio_id,
                ticker=ticker
            )
            return Response({
                "user_id": request.user.id,
                "portfolio_id": portfolio_id,
                "ticker": ticker,
                "currencies": currencies
            })
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

# Transaction
class PortfolioTransactionCreateView(generics.CreateAPIView):
    """
    Permet à un utilisateur authentifié de créer une transaction (achat/vente/dividende/intérêt/dépôt/retrait)
    sur un ticker présent dans l’un de ses portefeuilles, ou sans ticker si applicable.
    Valide dynamiquement les valeurs numériques et la cohérence de l'opération.
    """
    serializer_class = PortfolioTransactionCreateSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        data = request.data.copy()

        try:
            portfolio = Decimal(data["portfolio"])
            amount = Decimal(data["amount"])
            fees = Decimal(data["fees"])
            operation = data["operation"]

            if operation in ["buy", "sell"]:
                stock_price = Decimal(data["stock_price"])
                quantity = round(amount / stock_price, 6)
                currency = data["currency"]
                try:
                    portfolio_ticker = self.get_portfolio_ticker(data["portfolio_ticker"], data["portfolio"], request.user).pk
                except PortfolioTicker.DoesNotExist:
                    return Response({"detail": "Ticker not found in user's portfolio."}, status=status.HTTP_400_BAD_REQUEST)
            elif operation == "dividend":
                quantity = Decimal(data["quantity"])
                stock_price = None
                currency = data["currency"]
                try:
                    portfolio_ticker = self.get_portfolio_ticker(data["portfolio_ticker"], data["portfolio"], request.user).pk
                except PortfolioTicker.DoesNotExist:
                    return Response({"detail": "Ticker not found in user's portfolio."}, status=status.HTTP_400_BAD_REQUEST)
            elif operation == "interet":
                quantity = Decimal(data["quantity"])
                stock_price = None
                portfolio_ticker = None
                currency = data["currency"]
            elif operation in ["deposit", "withdrawal"]:
                quantity = None
                stock_price = None
                portfolio_ticker = None
                currency = data["currency"]
            else:
                return Response({"detail": "Opération non supportée."}, status=status.HTTP_400_BAD_REQUEST)

        except (ValueError, TypeError, InvalidOperation):
            return Response({"detail": "Invalid numeric value."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            if isinstance(data["date"], str):
                date = datetime.fromisoformat(data["date"]).date()
            elif isinstance(data["date"], datetime):
                date = data["date"].date()
            else:
                date = data["date"]
        except Exception:
            return Response({"detail": "Invalid date format."}, status=status.HTTP_400_BAD_REQUEST)

        # Recherche d'une transaction existante (si ticker présent)
        existing_tx = None
        if portfolio_ticker and operation in ["buy", "sell"]:
            existing_tx = PortfolioTransaction.objects.filter(
                portfolio=portfolio,
                portfolio_ticker=portfolio_ticker,
                date=date,
                stock_price=stock_price,
                operation=operation,
                currency=currency
            ).first()

        if existing_tx:
            existing_tx.amount += amount
            existing_tx.fees += fees
            existing_tx.quantity = round(existing_tx.amount / existing_tx.stock_price, 6)
            existing_tx.save()

            serializer = self.get_serializer(existing_tx)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        serializer_data = {
            "portfolio": portfolio,
            "portfolio_ticker": portfolio_ticker,
            "operation": operation,
            "date": date,
            "amount": round(amount, 2),
            "fees": fees,
            "stock_price": stock_price,
            "quantity": quantity,
            "currency": currency,
        }

        serializer = self.get_serializer(data=serializer_data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            print("❌ Serializer errors:", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get_portfolio_ticker(self, ticker, portfolio_id, user):
        return PortfolioTicker.objects.get(
            ticker=ticker,
            portfolio_id=portfolio_id,
            portfolio__user=user
        )

class PortfolioTransactionsView(APIView):
    """
    Récupère toutes les transactions associées à un portefeuille donné,
    appartenant à l'utilisateur authentifié.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, portfolio_id):
        portfolio = get_object_or_404(Portfolio, id=portfolio_id, user=request.user)

        transactions = PortfolioTransaction.objects.filter(
            portfolio=portfolio
        ).order_by("-date")

        serializer = PortfolioTransactionDetailSerializer(transactions, many=True)
        return Response(serializer.data)

class DeletePortfolioTransactionView(APIView):
    """
    Supprime une transaction d'un portefeuille appartenant à l'utilisateur connecté.
    """
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, transaction_id, *args, **kwargs):
        try:
            transaction = PortfolioTransaction.objects.get(
                id=transaction_id,
                portfolio_ticker__portfolio__user=request.user
            )
        except PortfolioTransaction.DoesNotExist:
            return Response(
                {"detail": "Transaction non trouvée."},
                status=status.HTTP_404_NOT_FOUND
            )

        transaction.delete()
        return Response(
            {"detail": "Transaction supprimée avec succès."},
            status=status.HTTP_204_NO_CONTENT
        )

class UpdatePortfolioTransactionView(UpdateAPIView):
    """
    Permettre à un utilisateur authentifié de modifier une transaction d'un de ses portefeuilles
    """
    queryset = PortfolioTransaction.objects.all()
    serializer_class = PortfolioTransactionUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return PortfolioTransaction.objects.filter(
            portfolio_ticker__portfolio__user=self.request.user
        )

    def update(self, request, *args, **kwargs):
        data = request.data.copy()
        data['quantity'] = round(float(data.get('quantity', 0)), 6)

        operation = data.get('operation')

        if operation in ["buy", "sell", "dividend"]:
            try:
                portfolio_ticker = PortfolioTicker.objects.get(
                    ticker=data['portfolio_ticker'],
                    portfolio_id=data['portfolio'],
                    portfolio__user=request.user
                )
            except PortfolioTicker.DoesNotExist:
                return Response(
                    {"detail": "Ticker not found in user's portfolio."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            data['portfolio_ticker'] = portfolio_ticker.pk

        # Pas besoin de gérer le portfolio_ticker pour deposit, withdrawal, interet

        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=data, partial=partial)

        if not serializer.is_valid():
            print("❌ Serializer errors:", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        self.perform_update(serializer)
        return Response(serializer.data)

class ExcelPortfolioTransactionUploadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        file_upload = request.FILES.get("file")
        if not file_upload:
            return html_error_response("Erreur d'import", ["Aucun fichier fourni."])
        
        portfolio = request.data.get("portfolioId")

        try:
            data = pd.read_excel(BytesIO(file_upload.read()), engine='openpyxl')
            data.columns = data.columns.str.strip()
        except Exception as e:
            return html_error_response("Erreur de lecture du fichier", [str(e)])

        expected_columns = [
            'Ticker', 'Type', 'Date',
            'Montant', "Prix de l'action lors de la transaction", 'Quantité', 'Frais', 'Devise'
        ]
        if not all(col in data.columns for col in expected_columns):
            lignes = [
                f"Colonnes attendues : {', '.join(expected_columns)}",
                f"Colonnes reçues : {', '.join(data.columns)}"
            ]
            return html_error_response("Colonnes Excel incorrectes", lignes)

        # Nettoyage des valeurs vides
        data['Ticker'] = data['Ticker'].fillna('')
        data['Devise'] = data['Devise'].fillna('')
        data['Date'] = pd.to_datetime(data['Date']).dt.date

        # Groupement des lignes similaires
        grouped = data.groupby([
            'Ticker',
            'Type',
            'Date',
            'Devise',
            "Prix de l'action lors de la transaction"
        ], as_index=False).agg({
            'Montant': 'sum',
            'Quantité': 'sum',
            'Frais': 'sum'
        })

        # Vérifie que tous les tickers sont bien dans le portefeuille
        tickers_in_excel = set(ticker for ticker in grouped['Ticker'].unique() if ticker.strip())

        # Récupère les tickers déjà présents dans le portefeuille de l'utilisateur
        existing_tickers = set(
            PortfolioTicker.objects.filter(
                portfolio_id=portfolio,
                portfolio__user=request.user
            ).values_list("ticker__ticker", flat=True)
        )
        # Détermine les tickers manquants
        missing_tickers = tickers_in_excel - existing_tickers
        # Si certains tickers ne sont pas dans le portefeuille, retourne une erreur HTML
        if missing_tickers:
            lignes = [
                "Les tickers suivants ne sont pas présents dans votre portefeuille :",
                "<ul>" + "".join(f"<li>{ticker}</li>" for ticker in sorted(missing_tickers)) + "</ul>",
                "Merci d'ajouter ces tickers avant d'importer le fichier."
            ]
            return html_error_response("Tickers manquants", lignes)


        to_create = []
        to_update = []
        for index, row in grouped.iterrows():
            operation = row['Type']
            date = row['Date']
            ticker = row['Ticker']
            currency = row.get("Devise")

            try:
                amount = Decimal(abs(float(row['Montant'])))
                fees = Decimal(abs(float(row['Frais'])))
                stock_price = Decimal(float(row["Prix de l'action lors de la transaction"]))
                quantity = Decimal(abs(float(row['Quantité'])))
            except Exception as e:
                return html_error_response(
                    f"Erreur ligne {index + 2}",
                    [f"Problème de conversion numérique : {str(e)}"]
                )

            portfolio_ticker = None
            if operation in ["buy", "sell", "dividend"]:
                try:
                    portfolio_ticker = PortfolioTicker.objects.get(
                        ticker=ticker,
                        currency=currency,
                        portfolio_id=portfolio,
                        portfolio__user=request.user
                    )
                except PortfolioTicker.DoesNotExist:
                    return html_error_response(
                        f"Erreur ligne {index + 2}",
                        [f"Le ticker <strong>{ticker}</strong> n'est pas présent dans votre portefeuille."]
                    )

            # Calcul de quantité si achat/vente
            if operation in ["buy", "sell"]:
                if stock_price == 0:
                    return html_error_response(
                        f"Erreur ligne {index + 2}",
                        ["Division par zéro : le prix de l'action est égal à 0."]
                    )
                if operation == "sell":
                    quantity = round((amount + fees) / stock_price, 6)
                else:
                    quantity = round(amount / stock_price, 6)

            # Recherche d'une transaction existante pour mise à jour éventuelle
            existing_tx = None
            if operation in ["buy", "sell", "dividend"]:
                existing_tx = PortfolioTransaction.objects.filter(
                    portfolio=portfolio,
                    portfolio_ticker=portfolio_ticker,
                    date=date,
                    stock_price=stock_price,
                    operation=operation,
                    currency=currency
                ).first()

            if existing_tx:
                new_amount = existing_tx.amount + amount
                new_fees = existing_tx.fees + fees
                if operation in ["buy", "sell"]:
                    new_quantity = round(new_amount / stock_price, 6)
                else:
                    new_quantity = quantity

                to_update.append((existing_tx, new_amount, new_fees, new_quantity))
            else:
                serializer_data = {
                    "portfolio": portfolio,
                    "operation": operation,
                    "date": date,
                    "amount": round(float(amount), 2),
                    "fees": round(float(fees), 2),
                    "quantity": round(float(quantity), 6),
                    "stock_price": round(float(stock_price), 2) if operation in ["buy", "sell"] else None,
                    "portfolio_ticker": portfolio_ticker.pk if portfolio_ticker else None,
                    "currency": currency,
                }

                serializer = PortfolioTransactionCreateSerializer(data=serializer_data, context={'request': request})
                if not serializer.is_valid():
                    return html_error_response(
                        f"Erreur ligne {index + 2}",
                        [f"Erreurs de validation : <pre>{serializer.errors}</pre>"]
                    )

                to_create.append(serializer)

        # ✅ Transaction atomique
        with transaction.atomic():
            for serializer in to_create:
                serializer.save()
            for instance, new_amount, new_fees, new_quantity in to_update:
                instance.amount = new_amount
                instance.fees = new_fees
                instance.quantity = new_quantity
                instance.save()

        return Response({"importées": len(to_create) + len(to_update)}, status=status.HTTP_201_CREATED)


# Portefeuille Performance
class UserPortfolios(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        portfolios_data = Portfolio.objects.filter(user=user).values("id", "name")
        portfolios = [{"id": p["id"], "name": p["name"]} for p in portfolios_data]

        return Response(portfolios)

class UserPortfolioPerformanceSummary(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        portfolios_data = Portfolio.objects.filter(user=user).exclude(name="all").values("id", "name")
        portfolios = [{"id": p["id"], "name": p["name"]} for p in portfolios_data]

        return Response(portfolios)

class PortfolioPerformanceDynamicView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, portfolio_id):
        requested_fields = request.query_params.get("fields")
        if not requested_fields:
            return Response({"error": "Missing `fields` parameter."}, status=status.HTTP_400_BAD_REQUEST)

        field_list = requested_fields.split(",")
        data = get_portfolio_performance_data(request.user, portfolio_id, field_list)

        if data is None:
            return Response({"error": "Performance not found."}, status=status.HTTP_404_NOT_FOUND)

        return Response(data, status=status.HTTP_200_OK)

class UserPortfolioPerformanceRepartitionAllPortfolio(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        portfolios = Portfolio.objects.filter(user=user).exclude(name="all").values_list('name', 'id')

        # Palette de 20 couleurs bien distinctes
        color_palette = [
            "#5863f8", "#c70039", "#5dd39e", "#fdfd96", "#6c5ce7",
            "#9467bd", "#00cec9", "#fa824c", "#00b894", "#ff7675", 
            "#ffa630", "#fd79a8", "#e17055", "#fab1a0", "#55efc4"
        ]

        chart_config = {
            "repartition": {
                "label": "Répartition",
            },
        }
        portfolios_valuation = []
        fields = ["portfolio_valuation"]

        for index, (portfolio_name, portfolio_id) in enumerate(portfolios):
            data = get_portfolio_performance_data(user, portfolio_id, fields)

            result = {}
            if data and isinstance(data.get("portfolio_valuation"), list) and len(data["portfolio_valuation"]) > 0:
                last_entry = data["portfolio_valuation"][-1]
                last_value = last_entry.get(portfolio_name)
                result["portfolio"] = portfolio_name
                result["repartition"] = last_value or 0
            else:
                result["portfolio"] = portfolio_name
                result["repartition"] = 0

            color = color_palette[index % len(color_palette)]
            result["fill"] = color

            chart_config[portfolio_name] = {
                "label": portfolio_name,
                "color": color
            }

            portfolios_valuation.append(result)

        total_valuation = sum(p["repartition"] for p in portfolios_valuation)

        portfolios_repartition = []
        for p in portfolios_valuation:
            percentage = (p["repartition"] / total_valuation * 100) if total_valuation > 0 else 0
            portfolios_repartition.append({
                "portfolio": p["portfolio"],
                "repartition": round(percentage, 2),
                "fill": p["fill"]
            })

        return Response((portfolios_repartition, chart_config), status=status.HTTP_200_OK)

class UserPortfolioPerformanceTwrDate(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, start_date, portfolio_id):
        tickers_valuations = request.data.get("tickers_valuations")
        start_date = pd.to_datetime(start_date)
        if not isinstance(tickers_valuations, dict):
            return Response({"error": "tickers_valuations must be a dictionary"}, status=400)
        
        portefeuille = PorfolioPerformances(user=request.user, portfolios=portfolio_id, start_date=start_date, tickers_valuations=tickers_valuations)
        
        return Response(portefeuille.get_twr())

class PortfolioPositionSummaryView(APIView):
    """
    Retourne un résumé par ticker d'un portefeuille,
    avec toutes les informations financières et comparatives
    basées sur TickerPerformanceCompareSP500.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, portfolio_id):
        user = request.user

        # Vérifie que le portefeuille appartient à l'utilisateur
        portfolio = get_object_or_404(Portfolio, id=portfolio_id, user=user)

        # Récupère tous les tickers du portefeuille
        tickers = PortfolioTicker.objects.filter(portfolio=portfolio)

        result = []

        for pt in tickers:
            # Dernière performance pour ce ticker
            perf = TickerPerformanceCompareSP500.objects.filter(
                user=user, portfolio=portfolio, ticker=pt
            ).order_by("-calculated_at").first()

            if not perf:
                continue  # on ignore les tickers sans performance

            company = pt.ticker  # lien vers Company
            logo_url = request.build_absolute_uri(f"/static/logos/{company.ticker}.png")

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
                "currency": dict(CURRENCY_CHOICES).get(perf.currency, perf.currency),
            })

        # Tri en décroissant sur value
        result_sorted = sorted(result, key=lambda x: x["value"], reverse=True)

        return Response(result_sorted)
    
class PortfolioTransactionCompareDetailView(APIView):
    """
    Retourne les performances détaillées d'un ticker précis d'un portefeuille,
    avec toutes les transactions et comparaisons SP500.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, portfolio_id, ticker):
        user = request.user

        # Vérifie que le portefeuille appartient à l'utilisateur
        portfolio = get_object_or_404(Portfolio, id=portfolio_id, user=user)

        # Récupère le PortfolioTicker correspondant au ticker demandé
        portfolio_ticker = get_object_or_404(
            PortfolioTicker,
            portfolio=portfolio,
            ticker__ticker=ticker
        )

        # Récupère toutes les transactions pour ce ticker
        transactions = TransactionCompareSP500.objects.filter(
            user=user,
            portfolio=portfolio,
            ticker=portfolio_ticker
        ).order_by("date")  # tri par date croissante

        if not transactions.exists():
            return Response({"error": "No transactions found for this ticker."}, status=404)
        
        logo_url = request.build_absolute_uri(f"/static/logos/{ticker}.png")

        result = []
        for idx, tx in enumerate(transactions, start=1):
            result.append({
                "id": idx,  # compteur à la place de tx.id
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
            })

        # Tri en décroissant sur amountInvest
        result_sorted = sorted(result, key=lambda x: x["dateBuy"], reverse=True)

        return Response(result_sorted)

class PortfolioAllTransactionsCompareDetailView(APIView):
    """
    Retourne les performances détaillées de toutes les transactions d'un portefeuille,
    avec toutes les comparaisons SP500.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, portfolio_id):
        user = request.user

        # Vérifie que le portefeuille appartient à l'utilisateur
        portfolio = get_object_or_404(Portfolio, id=portfolio_id, user=user)

        # Récupère tous les tickers du portefeuille
        portfolio_tickers = PortfolioTicker.objects.filter(portfolio=portfolio)

        result = []

        for ticker_obj in portfolio_tickers:
            ticker = ticker_obj.ticker.ticker
            logo_url = request.build_absolute_uri(f"/static/logos/{ticker}.png")

            # Récupère toutes les transactions pour ce ticker, tri croissant
            transactions = TransactionCompareSP500.objects.filter(
                user=user,
                portfolio=portfolio,
                ticker=ticker_obj
            ).order_by("date", "id")  # trier par date puis par id pour stabilité

            for tx in transactions:
                result.append({
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
                })

        # Numérotation unique globale de la plus ancienne à la plus récente
        result_sorted = sorted(result, key=lambda x: (x["dateBuy"], x["ticker"]))
        for idx, tx in enumerate(result_sorted, start=1):
            tx["id"] = idx

        # Tri final pour l'affichage : de la plus récente à la plus ancienne
        result_display = sorted(result_sorted, key=lambda x: x["id"], reverse=True)

        return Response(result_display)

class PortfolioTickerPerformanceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, portfolio_id):
        user = request.user

        # Récupérer le dernier calculated_at par ticker pour ce portefeuille
        latest_perfs = (
            TickerPerformanceCompareSP500.objects.filter(
                portfolio__user=user,
                portfolio__id=portfolio_id
            )
            .values('ticker')  # group by ticker
            .annotate(latest_id=Max('id'))  # récupérer la dernière entrée
        )

        # Récupérer les objets complets
        performances = TickerPerformanceCompareSP500.objects.filter(
            id__in=[item['latest_id'] for item in latest_perfs]
        )

        result = {"Montant": [], "%": [], "% / an": [], "sp500": []}

        for perf in performances:
            if not perf.ticker:
                continue
            company = perf.ticker.ticker  # PortfolioTicker -> Company
            company_name = company.name
            ticker_symbol = company.ticker
            logo_url = request.build_absolute_uri(f"/static/logos/{company.ticker}.png")
            
            # Montant en euros
            amount_value = float(perf.total_gain)
            if perf.currency != "EUR":
                amount_value = StockPrice.convert_price(
                    amount_value,
                    from_currency=perf.currency,
                    to_currency="EUR",
                    date=perf.calculated_at
                )

            result["Montant"].append({
                "companyName": company_name,
                "ticker": ticker_symbol,
                "logoUrl": logo_url,
                "value": float(perf.total_gain),
            })
            result["%"].append({
                "companyName": company_name,
                "ticker": ticker_symbol,
                "logoUrl": logo_url,
                "value": float(perf.gain_percentage),
            })
            result["% / an"].append({
                "companyName": company_name,
                "ticker": ticker_symbol,
                "logoUrl": logo_url,
                "value": float(perf.annualized_return),
            })
            result["sp500"].append({
                "companyName": company_name,
                "ticker": ticker_symbol,
                "logoUrl": logo_url,
                "value": float(perf.performance_gap),
            })

        # Tri décroissant par "value" pour chaque sous-liste
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
        if field.name not in ["id", "user", "portfolio", "calculated_at"]
    }

    data = {}
    for field in fields:
        clean_field = field.strip()
        if clean_field in valid_fields:
            data[clean_field] = getattr(performance, clean_field)
        else:
            data[clean_field] = None  # ou logguer un avertissement
    return data

