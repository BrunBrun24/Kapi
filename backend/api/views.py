from datetime import datetime
from decimal import Decimal, InvalidOperation
from io import BytesIO
from django.http import HttpResponseServerError
from django.shortcuts import get_object_or_404
import pandas as pd
from rest_framework import generics, permissions, status
from rest_framework.generics import UpdateAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from django.db import transaction

from .models import (
    CURRENCY_CHOICES,
    Company,
    StockPrice,
    UserPreference,
    Portfolio,
    PortfolioTicker,
    PortfolioTransaction,
    PortfolioDepositOfMoney
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

class AvailablePortfolioTickersView(APIView):
    """
    Retourne tous les tickers qui ne sont pas encore associés à un portefeuille donné.
    Nécessite l'identifiant du portefeuille.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, portfolio_id, *args, **kwargs):
        # Vérifier que le portefeuille appartient bien à l'utilisateur
        try:
            portfolio = Portfolio.objects.get(id=portfolio_id, user=request.user)
        except Portfolio.DoesNotExist:
            return Response({"detail": "Portfolio not found."}, status=404)

        # Tickers déjà présents dans ce portefeuille
        existing_tickers = PortfolioTicker.objects.filter(portfolio=portfolio).values_list("ticker__ticker", flat=True)

        # Tous les tickers sauf ceux déjà associés
        available_companies = Company.objects.exclude(ticker__in=existing_tickers)

        data = [
            {"ticker": company.ticker, "name": company.name}
            for company in available_companies
        ]

        return Response(data)

class DeletePortfolioTickerView(APIView):
    """
    Supprime un ticker d'un portefeuille appartenant à l'utilisateur connecté.
    """
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, portfolio_id, ticker, *args, **kwargs):
        try:
            portfolio_ticker = PortfolioTicker.objects.get(
                portfolio__id=portfolio_id,
                portfolio__user=request.user,
                ticker__ticker=ticker
            )
        except PortfolioTicker.DoesNotExist:
            return Response(
                {"detail": "PortfolioTicker not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        portfolio_ticker.delete()
        return Response(
            {"detail": "PortfolioTicker deleted successfully."},
            status=status.HTTP_204_NO_CONTENT
        )


# Transaction
class PortfolioTransactionCreateView(generics.CreateAPIView):
    """
    Permet à un utilisateur authentifié de créer une transaction (achat/vente)
    sur un ticker présent dans l’un de ses portefeuilles.
    Fait des validations supplémentaires sur les valeurs numériques et
    la présence du ticker dans le portefeuille utilisateur.
    """
    serializer_class = PortfolioTransactionCreateSerializer
    permission_classes = [IsAuthenticated]

    
    def create(self, request, *args, **kwargs):
        data = request.data.copy()

        try:
            amount = Decimal(data["amount"])
            fees = Decimal(data["fees"])
            stock_price = Decimal(data["stock_price"])
            if data["operation"] in ["buy", "sell"]:
                quantity = round(amount / stock_price, 6)
            else:
                quantity = data["quantity"]
        except (ValueError, TypeError, InvalidOperation):
            return Response({"detail": "Invalid numeric value."}, status=status.HTTP_400_BAD_REQUEST)

        # Vérification du ticker
        try:
            portfolio_ticker = PortfolioTicker.objects.get(
                ticker=data["portfolio_ticker"],
                portfolio__user=request.user
            )
        except PortfolioTicker.DoesNotExist:
            return Response({"detail": "Ticker not found in user's portfolio."}, status=status.HTTP_400_BAD_REQUEST)

        # Formatage correct de la date
        try:
            if isinstance(data["date"], str):
                date = datetime.fromisoformat(data["date"]).date()
            elif isinstance(data["date"], datetime):
                date = data["date"].date()
            else:
                date = data["date"]
        except Exception:
            return Response({"detail": "Invalid date format."}, status=status.HTTP_400_BAD_REQUEST)

        # 🔍 Recherche d'une transaction existante
        existing_tx = PortfolioTransaction.objects.filter(
            portfolio_ticker=portfolio_ticker,
            date=date,
            stock_price=stock_price,
            operation=data["operation"]
        ).first()

        if existing_tx:
            print("existe")
            existing_tx.amount += amount
            existing_tx.fees += fees
            existing_tx.quantity = round(existing_tx.amount / existing_tx.stock_price, 6)
            existing_tx.save()

            serializer = self.get_serializer(existing_tx)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        # ✅ Création d'une nouvelle transaction
        serializer_data = {
            "portfolio_ticker": portfolio_ticker.pk,
            "operation": data["operation"],
            "date": date,
            "amount": amount,
            "fees": fees,
            "stock_price": stock_price,
            "quantity": quantity,
            "notes": data.get("notes", "")
        }

        serializer = self.get_serializer(data=serializer_data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            print("❌ Serializer errors:", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AllUserTransactionsView(APIView):
    """
    Récupère toutes les transactions de tous les portefeuilles de l'utilisateur connecté.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        transactions = PortfolioTransaction.objects.filter(
            portfolio_user=request.user
        ).select_related("portfolio_ticker", "portfolio_ticker__portfolio")
        
        serializer = PortfolioTransactionDetailSerializer(transactions, many=True)
        return Response(serializer.data)

class UserPortefeuilleTransactionsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, portfolio_id):
        get_object_or_404(Portfolio, id=portfolio_id, user=request.user)

        transactions = PortfolioTransaction.objects.filter(
            portfolio_ticker__portfolio_id=portfolio_id
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
                portfolio_user=request.user
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

class UpdateTransactionView(UpdateAPIView):
    """
    Permettre à un utilisateur authentifié de modifier une transaction d'un de ses portefeuilles
    """
    queryset = PortfolioTransaction.objects.all()
    serializer_class = PortfolioTransactionUpdateSerializer

    def update(self, request, *args, **kwargs):
        data = request.data.copy()
        data['quantity'] = round(float(data.get('quantity', 0)), 6)

        try:
            portfolio_ticker = PortfolioTicker.objects.get(
                ticker=data['portfolio_ticker'],
                portfolio__user=request.user
            )
        except PortfolioTicker.DoesNotExist:
            return Response(
                {"detail": "Ticker not found in user's portfolio."},
                status=status.HTTP_400_BAD_REQUEST
            )

        data['portfolio_ticker'] = portfolio_ticker.pk

        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=data, partial=partial)

        if not serializer.is_valid():
            print("❌ Serializer errors:", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        self.perform_update(serializer)
        return Response(serializer.data)

class ExcelTransactionUploadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        file_upload = request.FILES.get("file")
        if not file_upload:
            return Response({"detail": "Aucun fichier fourni."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            data = pd.read_excel(BytesIO(file_upload.read()), engine='openpyxl')
            data.columns = data.columns.str.strip()
        except Exception as e:
            return Response({"detail": f"Erreur de lecture du fichier : {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

        expected_columns = [
            'Ticker', 'Type', 'Date',
            'Montant', "Prix de l'action lors de la transaction", 'Quantité', 'Frais'
        ]
        if not all(col in data.columns for col in expected_columns):
            return Response({
                "detail": f"Colonnes attendues : {expected_columns}",
                "reçues": list(data.columns)
            }, status=status.HTTP_400_BAD_REQUEST)

        # 🧠 Combine les lignes similaires
        data['Date'] = pd.to_datetime(data['Date']).dt.date
        grouped = data.groupby([
            'Ticker', 
            'Type', 
            'Date', 
            "Prix de l'action lors de la transaction",
        ], as_index=False).agg({
            'Montant': 'sum',
            'Quantité': 'sum',
            'Frais': 'sum'
        })

        to_create = []
        to_update = []

        for index, row in grouped.iterrows():
            try:
                portfolio_ticker = PortfolioTicker.objects.get(
                    ticker=row['Ticker'],
                    portfolio__user=request.user
                )
            except PortfolioTicker.DoesNotExist:
                html_error = f"<h2>Erreur ligne {index + 2}</h2><br><p>Ticker {row['Ticker']} introuvable dans votre portefeuille.</p>"
                return HttpResponseServerError(html_error)

            operation = row['Type']
            date = row['Date']
            try:
                amount = Decimal(abs(float(row['Montant'])))
                fees = Decimal(abs(float(row['Frais'])))
                stock_price = Decimal(float(row["Prix de l'action lors de la transaction"]))
                if operation in ["buy", "sell"]:
                    try:
                        quantity = round((amount - fees) / stock_price, 6)
                    except ZeroDivisionError:
                        return Response({"detail": f"Erreur division par zéro ligne {index + 2} (prix d'action à 0)."}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    quantity = Decimal(abs(float(row['Quantité'])))
            except Exception as e:
                return Response({"detail": f"Erreur de conversion ligne {index + 2}: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

            # Recherche transaction existante
            existing_tx = PortfolioTransaction.objects.filter(
                portfolio_ticker=portfolio_ticker,
                date=date,
                stock_price=stock_price,
                operation=operation
            ).first()

            if existing_tx:
                # Préparer la MAJ
                new_amount = existing_tx.amount + amount
                new_fees = existing_tx.fees + fees
                if operation in ["buy", "sell"]:
                    new_quantity = round(new_amount / stock_price, 6)
                else:
                    new_quantity = 0

                # Pas besoin de sérialiseur, juste validation manuelle si tu veux
                to_update.append((existing_tx, new_amount, new_fees, new_quantity))
            else:
                # Sérialiseur pour validation complète
                serializer_data = {
                    "portfolio_ticker": portfolio_ticker.pk,
                    "operation": operation,
                    "date": date,
                    "amount": abs(float(row['Montant'])),
                    "stock_price": round(float(row["Prix de l'action lors de la transaction"]), 2),
                    "quantity": float(quantity),
                    "fees": abs(float(row['Frais'])),
                    "notes": ""
                }

                serializer = PortfolioTransactionCreateSerializer(data=serializer_data, context={'request': request})
                if not serializer.is_valid():
                    html_error = f"<h2>Erreur ligne {index + 2}</h2><pre>{serializer.errors}</pre>"
                    return HttpResponseServerError(html_error)

                to_create.append(serializer)

        # ✅ Si on arrive ici, toutes les lignes sont valides → exécution dans une seule transaction
        with transaction.atomic():
            for serializer in to_create:
                serializer.save()

            for instance, new_amount, new_fees, new_quantity in to_update:
                instance.amount = new_amount
                instance.fees = new_fees
                instance.quantity = new_quantity
                instance.save()

        return Response({"importées": len(to_create) + len(to_update)}, status=status.HTTP_201_CREATED)

    

class TickerListView(APIView):
    """
    Récupère la liste de toutes les entreprises disponibles avec leurs tickers.
    Accessible sans authentification.
    """
    def get(self, request, *args, **kwargs):
        companies = Company.objects.all()
        tickers = [{"ticker": company.ticker, "name": company.name} for company in companies]
        return Response(tickers)

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
    