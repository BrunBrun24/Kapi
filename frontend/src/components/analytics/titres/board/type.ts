export type TableDataTicker = {
  id: number; // primary key
  logo: string;

  ticker: string;
  dateBuy: Date;
  amount: number;
  stockValue: number;

  gains: number;
  gainsPercentage: number;

  gainsSP500: number;
  gainsPercentageSP500: number;
  difference: number;

  durationDay: number;
  annualizedPercentage: number;

  capitalGainOrLoss: number;
  capitalGainOrLossPercentage: number;

  dividendAmount: number;
  dividendYieldPercentage: number;

  quantity: number;
  pru: number;
  fees: number;
};

export type TableDataPosition = {
  ticker: string; // primary key
  name: string;
  nbBuy: number;
  logo: string;
  currency: string;

  amountInvest: number;
  value: number;

  gains: number;
  gainsPercentage: number;

  gainsSP500: number;
  gainsPercentageSP500: number;
  difference: number;

  durationDay: number;
  annualizedPercentage: number;

  capitalGainOrLoss: number;
  capitalGainOrLossPercentage: number;

  dividendAmount: number;
  dividendYieldPercentage: number;

  quantity: number;
  fees: number;
};

export type TableDataTransaction = {
  id: number; // primary key

  ticker: string;
  name: string;
  logo: string;

  date: Date;
  type: "buy" | "sell";
  quantity: number;
  amountInvest: number;
  stockValue: number;
  fees: number;
};
