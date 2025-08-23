// Un objet représentant une entrée avec une date et des valeurs par portefeuille (clé dynamique)
export type PortfolioEntry = {
  date: string;
  [portfolioName: string]: number | string; // la clé "date" est string, les autres valeurs sont number ou string
};

// Les différentes données de performance par type de métrique, chaque champ est un tableau d'entries
export type PortfolioPerformanceData = {
  tickers_invested_amounts: PortfolioEntry[];
  tickers_sold_amounts: PortfolioEntry[];
  tickers_twr: PortfolioEntry[];
  tickers_gain: PortfolioEntry[];
  tickers_valuation: PortfolioEntry[];
  ticker_invested_amounts: PortfolioEntry[];
  tickers_dividends: PortfolioEntry[];
  tickers_pru: PortfolioEntry[];

  portfolio_twr: PortfolioEntry[];
  portfolio_gain: PortfolioEntry[];
  portfolio_monthly_percentages: PortfolioEntry[];
  portfolio_valuation: PortfolioEntry[];
  portfolio_invested_amounts: PortfolioEntry[];
  
  portfolio_cash: PortfolioEntry[];
  portfolio_fees: PortfolioEntry[];
  portfolio_cagr: Record<string, Record<string, number | null>>;
  portfolio_dividend_yield: Record<string, number | null>;
  portfolio_dividend_earn: Record<string, number | null>;
};

// Le type global de la réponse API : un objet indexé par nom de portefeuille
// Chaque clé (sauf "portfolios") est un PortfolioPerformanceData,
// la clé "portfolios" contient la liste des portefeuilles disponibles
export type PortfolioData = {
  [portfolioName: string]: PortfolioPerformanceData;
};

// Typage pour les props dans React, on peut avoir un data ou undefined
export type PortfolioPerformances = {
  performanceData?: PortfolioData | undefined;
  portfolioName?: string; // tu utilises "id" qui est une string, donc je mets string ici
  dataPortfolio?: UserPortfolio;
};

export type UserPortfolio = {
  id: string;
  name: string;
};

export type SelectedPortfolio = {
  selectedPortfolio?: UserPortfolio;
};

export const portfolioGlobalName = "all";

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
  }
};
