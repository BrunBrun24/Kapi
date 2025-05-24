import type { ReactNode } from "react";

export interface Portfolio {
  id: string;
  name: string;
  lastModified: number;
}

export interface Transaction {
  symbol: ReactNode;
  id: string;
  portfolioId: string;
  ticker: string;
  name: string;
  operation: "buy" | "sell";
  stock_price: number;
  quantity: number;
  amount: number;
  date: string;
  fees?: number;
  notes?: string;
}

export interface PortfolioState {
  portfolios: Portfolio[];
  selectedPortfolioId: string | null;
  transactions: Transaction[];
}

export interface Ticker {
  ticker: string;
  name: string;
  currency: string;
  logo: string;
}

export interface TickerNotInPortfolio {
  ticker: string;
  name: string;
}

export interface Currency {
  code: string;
  label: string;
}

export interface PortfolioIdProps {
  selectedPortfolioId: string | null;
}
