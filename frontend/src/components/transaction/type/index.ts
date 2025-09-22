import type { ReactNode } from "react";

export interface Portfolio {
  id: string;
  name: string;
}

export interface Transaction {
  symbol: ReactNode;
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
  stock_price: number;
  quantity: number;
  amount: number;
  date: string;
  fees: number;
  currency: string;
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
  currencies: string[];
}

export interface Currency {
  code: string;
  label: string;
}
