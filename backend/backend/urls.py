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
    ExcelPortfolioTransactionUploadView, PortfolioAllTransactionsCompareDetailView, PortfolioDetailView, PortfolioListCreateView, 
    PortfolioPerformanceDynamicView, PortfolioPositionSummaryView, PortfolioTickerAvailableView, 
    PortfolioTickerCurrenciesView, PortfolioTickerDeleteView, PortfolioTickerListCreateView, 
    PortfolioTickerPerformanceView, PortfolioTransactionCompareDetailView, PortfolioTransactionDetailUpdateDeleteView, PortfolioTransactionListCreateView, UserPortfolioPerformanceRepartitionAllPortfolio, 
    UserPortfolioPerformanceSummary, UserPortfolioPerformanceTwrDate, UserPortfolios, CurrencyListView, CurrencyTickerView, UserCreateView
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/user/register/", UserCreateView.as_view()),
    path("api/token/", TokenObtainPairView.as_view()),
    path("api/token/refresh/", TokenRefreshView.as_view()),
    path("api-auth/", include("rest_framework.urls")),
    path("api/", include("api.urls")),

    # Portefeuille
    path("api/portfolios/", PortfolioListCreateView.as_view()),
    path("api/portfolios/<int:pk>/", PortfolioDetailView.as_view()),

    # Portefeuille Ticker
    path('api/portfolios/<int:portfolio_id>/tickers/', PortfolioTickerListCreateView.as_view()),
    path('api/portfolios/<int:portfolio_id>/tickers/available/', PortfolioTickerAvailableView.as_view()),
    path('api/portfolios/<int:portfolio_id>/tickers/<str:ticker>/currencies/', PortfolioTickerCurrenciesView.as_view()),
    path('api/portfolios/<int:portfolio_id>/tickers/<str:ticker>/<str:currency>/', PortfolioTickerDeleteView.as_view()),

    # Transaction
    path("api/portfolios/<int:portfolio_id>/transactions/", PortfolioTransactionListCreateView.as_view()),
    path("api/transactions/<int:pk>/", PortfolioTransactionDetailUpdateDeleteView.as_view()),
    path("api/portfolios/<int:portfolio_id>/transactions/upload-excel/", ExcelPortfolioTransactionUploadView.as_view()),




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
