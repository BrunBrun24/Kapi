"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home)
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view())
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from api.views import (
    AddPortfolioTickerView, PortfolioAllTransactionsCompareDetailView, PortfolioPerformanceDynamicView, PortfolioPositionSummaryView, PortfolioTickerCurrenciesView, PortfolioTickerPerformanceView, PortfolioTransactionCompareDetailView, UserPortfolioPerformanceRepartitionAllPortfolio, UserPortfolioPerformanceSummary, UserPortfolioPerformanceTwrDate, UserPortfolios, PortfolioAvailableTickersView, CreatePortfolioView, CurrencyListView, CurrencyTickerView, DeletePortfolioTickerView, DeletePortfolioTransactionView, DeletePortfolioView, ExcelPortfolioTransactionUploadView, PortfolioTickersView, PortfolioTransactionCreateView ,
    UserCreateView, UpdatePortfolioTransactionView, UserPortfoliosView, PortfolioTransactionsView, UpdatePortfolioView
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/user/register/", UserCreateView.as_view()),
    path("api/token/", TokenObtainPairView.as_view()),
    path("api/token/refresh/", TokenRefreshView.as_view()),
    path("api-auth/", include("rest_framework.urls")),
    path("api/", include("api.urls")),

    # Portefeuille
    path("api/portfolio/create/", CreatePortfolioView.as_view()),
    path('api/portfolios/', UserPortfoliosView.as_view()),
    path('api/portfolios/<int:portfolio_id>/delete/', DeletePortfolioView.as_view()),
    path('api/portfolio/<int:pk>/update/', UpdatePortfolioView.as_view()),

    # Portefeuille Ticker
    path('api/portfolio/ticker/', AddPortfolioTickerView.as_view()),
    path("api/portfolio/<int:portfolio_id>/ticker/<str:ticker>/<str:currency>/delete/", DeletePortfolioTickerView.as_view()),
    path('api/portfolio/<int:portfolio_id>/tickers/', PortfolioTickersView.as_view()),
    path('api/portfolio/<int:portfolio_id>/available-tickers/', PortfolioAvailableTickersView.as_view()),
    path("api/portfolio/<int:portfolio_id>/ticker/<str:ticker>/currencies/", PortfolioTickerCurrenciesView.as_view()),

    # Transaction
    path("api/portfolio-transaction/create/", PortfolioTransactionCreateView .as_view()),
    path("api/portfolio-transaction/<int:portfolio_id>", PortfolioTransactionsView.as_view()),
    path("api/portfolio-transaction/<int:transaction_id>/delete", DeletePortfolioTransactionView.as_view()),
    path("api/portfolio-transaction/<int:pk>/update", UpdatePortfolioTransactionView.as_view()),
    path("api/upload-excel/transaction/", ExcelPortfolioTransactionUploadView.as_view()),

    # Portefeuille Performance
    path("api/user/portfolio/utilisateur/", UserPortfolioPerformanceSummary.as_view()),
    path("api/portfolio-performance/<int:portfolio_id>/", PortfolioPerformanceDynamicView.as_view()),
    path("api/portfolio-performance/portfolio/repartition/", UserPortfolioPerformanceRepartitionAllPortfolio.as_view()),
    path("api/portfolio-performance/twr/<str:start_date>/<int:portfolio_id>/", UserPortfolioPerformanceTwrDate.as_view()),

    path('api/portfolio-performance/tickers-performances/<int:portfolio_id>/', PortfolioPositionSummaryView.as_view()),
    path('api/portfolio-performance/ticker-transaction-performances/<int:portfolio_id>/<str:ticker>/', PortfolioTransactionCompareDetailView.as_view()),
    path('api/portfolio-performance/all-ticker-transactions/<int:portfolio_id>/', PortfolioAllTransactionsCompareDetailView.as_view()),
    path("api/portfolio/<int:portfolio_id>/performances/", PortfolioTickerPerformanceView.as_view()),

    # Annexe
    path("api/currencies/", CurrencyListView.as_view()),
    path("api/ticker/currency/", CurrencyTickerView.as_view()),


    path('api/user/portfolio/', UserPortfolios.as_view()),

]
