"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from api.views import (
    AddPortfolioTickerView, AllUserTransactionsView, AvailablePortfolioTickersView, CreatePortfolioView, CurrencyListView, CurrencyTickerView, DeletePortfolioTickerView, DeletePortfolioTransactionView, DeletePortfolioView, ExcelTransactionUploadView, PortfolioTickersView, PortfolioTransactionCreateView ,
    CreateUserView, UpdateTransactionView, UserPortfoliosView, UserPortefeuilleTransactionsView, UpdatePortfolioView, TickerListView
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/user/register/", CreateUserView.as_view(), name="register"),
    path("api/token/", TokenObtainPairView.as_view(), name="get_token"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="refresh"),
    path("api-auth/", include("rest_framework.urls")),
    path("api/", include("api.urls")),

    # Portefeuille
    path("api/portfolio/create/", CreatePortfolioView.as_view()),
    path('api/portfolio/get/', UserPortfoliosView.as_view(), name='user-portfolios'),
    path('portfolios/<int:portfolio_id>/delete/', DeletePortfolioView.as_view(), name='delete-portfolio'),
    path('api/portfolio/update/<int:pk>/', UpdatePortfolioView.as_view(), name='update-portfolio'),

    # Portefeuille Ticker
    path('api/portfolio/ticker/', AddPortfolioTickerView.as_view()),
    path("api/portfolio/<int:portfolio_id>/ticker/<str:ticker>/delete/", DeletePortfolioTickerView.as_view()),
    path('api/portfolio/<int:portfolio_id>/tickers/', PortfolioTickersView.as_view(), name='portfolio-tickers'),
    path('api/portfolio/<int:portfolio_id>/available-tickers/', AvailablePortfolioTickersView.as_view()),

    # Transaction
    path("api/portfolio-transaction/create/", PortfolioTransactionCreateView .as_view()),
    path("api/portfolio-transaction/get/<int:portfolio_id>", UserPortefeuilleTransactionsView.as_view(), name="user-transactions"),
    path("api/portfolio-transaction/all/", AllUserTransactionsView.as_view(), name="user-transaction-all"),
    path("api/portfolio-transaction/<int:transaction_id>/delete", DeletePortfolioTransactionView.as_view(), name="delete-transactions"),
    path("api/portfolio-transaction/<int:pk>/update", UpdateTransactionView.as_view(), name="update-transactions"),

    # Company
    path('api/tickers/', TickerListView.as_view(), name='get_all_tickers'),

    # Excel
    path("api/upload-excel/transaction/", ExcelTransactionUploadView.as_view()),

    # Annexe
    path("api/currencies/", CurrencyListView.as_view(), name="currency-list"),
    path("api/ticker/currency/", CurrencyTickerView.as_view())

]
