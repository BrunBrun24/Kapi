import type { JSX } from "react";

// Un portefeuille
export interface Portfolio {
  id: string;
  name: string;
}

// Transaction liée à un portefeuille
export interface PortfolioTransaction {
  id: string;
  portfolioId: string;
  ticker: string;
  name: string;
  operation:
    | "buy"
    | "sell"
    | "dividend"
    | "interest"
    | "deposit"
    | "withdrawal";
  stockPrice: number;
  quantity: number;
  amount: number;
  date: string;
  fees: number;
  currency: string;
  symbol: string | JSX.Element;
}

// Ticker présent dans un portefeuille
export interface PortfolioTicker {
  ticker: string;
  name: string;
  currency: string;
  logo: string;
}

// Ticker disponible mais non détenu
export interface AvailableTicker {
  ticker: string;
  name: string;
  currencies: string[];
}

// Devise
export interface Currency {
  code: string;
  label: string;
}
