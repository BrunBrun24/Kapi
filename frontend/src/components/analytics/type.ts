// Une entrée temporelle : date + valeurs numériques par portefeuille
export type PortfolioEntry = {
  date: number;
  [portfolioName: string]: number; // uniquement numérique
};

// Alias pour plus de lisibilité
type TimeSeries = PortfolioEntry[];
type PortfolioMetric = Record<string, number | null>;

// Données de performance pour un portefeuille
export type PortfolioPerformanceData = {
  // Séries temporelles (évolution dans le temps)
  tickers_invested_amounts_series: TimeSeries;
  tickers_sold_amounts_series: TimeSeries;
  tickers_twr_series: TimeSeries;
  tickers_gain_series: TimeSeries;
  tickers_valuation_series: TimeSeries;
  tickers_dividends_series: TimeSeries;
  tickers_pru_series: TimeSeries;

  portfolio_twr_series: TimeSeries;
  portfolio_gain_series: TimeSeries;
  portfolio_monthly_percentages_series: TimeSeries;
  portfolio_valuation_series: TimeSeries;
  portfolio_invested_amounts_series: TimeSeries;
  portfolio_cash_series: TimeSeries;
  portfolio_fees_series: TimeSeries;

  // Valeurs uniques / agrégats
  portfolio_cagr_metric: Record<string, PortfolioMetric>; // par année
  portfolio_dividend_yield_metric: PortfolioMetric;
  portfolio_dividend_earn_metric: PortfolioMetric;
};

// Objet global renvoyé par l’API : clé = nom du portefeuille
export type PortfolioData = {
  [portfolioName: string]: PortfolioPerformanceData;
};

// Props pour React
export type PortfolioPerformances = {
  performanceData?: PortfolioData;
  portfolioName?: string;
  dataPortfolio?: UserPortfolio;
};

// Portefeuilles utilisateurs
export type UserPortfolio = {
  id: string;
  name: string;
};

export type SelectedPortfolio = {
  selectedPortfolio: UserPortfolio;
};

// Nom réservé pour le portefeuille global
export const portfolioGlobalName = "all";

// Données affichées dans une carte (vue synthétique)
export type PortfolioCardData = {
  data: {
    info: {
      name: string;
      since: string;
      fees: string;
      balance: string;
    };
    totalValue: {
      currentValue: string;
      invested: string;
      gainPercentage: string;
    };
    performance: {
      capitalGain: string;
      cagr: string;
    };
    dividends: {
      received: string;
      yield: string;
    };
  };
};
