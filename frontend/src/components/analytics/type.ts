// Un objet représentant une entrée avec une date et des valeurs par portefeuille (clé dynamique)
export type PortfolioEntry = {
  date: string;
  [portfolioName: string]: number | string; // la clé "date" est string, les autres valeurs sont number ou string
};

// Les différentes données de performance par type de métrique, chaque champ est un tableau d'entries
export type PortfolioPerformanceData = {
  twr_by_ticker: PortfolioEntry[];
  net_price_by_ticker: PortfolioEntry[];
  gross_price_by_ticker: PortfolioEntry[];
  invested_by_ticker: PortfolioEntry[];
  sold_by_ticker: PortfolioEntry[];
  dividends_by_ticker: PortfolioEntry[];

  portfolio_twr: PortfolioEntry[];
  net_portfolio_price: PortfolioEntry[];
  monthly_percentage: PortfolioEntry[];
  bank_balance: PortfolioEntry[];
  total_invested: PortfolioEntry[];
  cash: PortfolioEntry[];
};

// Le type global de la réponse API : un objet indexé par nom de portefeuille
// Chaque clé (sauf "portfolios") est un PortfolioPerformanceData,
// la clé "portfolios" contient la liste des portefeuilles disponibles
export type PortfolioData = {
  [portfolioName: string]: PortfolioPerformanceData;
};

// Typage pour les props dans React, on peut avoir un data ou undefined
export type PortfolioPerformances = {
  performanceData: PortfolioData | undefined;
  portfolioId?: string; // tu utilises "id" qui est une string, donc je mets string ici
};

export type UserPortfolio = {
  id: string;
  name: string;
};

export const portfolioGlobalName = "My Portfolio";

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
