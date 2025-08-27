import {
  IconCash,
  IconTrendingDown,
  IconTrendingUp,
} from "@tabler/icons-react";

import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

import {
  portfolioGlobalName,
  UserPortfolio,
} from "@/components/analytics/type";
import { useEffect, useState } from "react";
import api from "@/api";

type CardsSummaryProps = {
  selectedPortfolio?: UserPortfolio;
};

export function CardsSummary({ selectedPortfolio }: CardsSummaryProps) {
  const [portfolioValuation, setPortfolioValuation] = useState<Array<Record<string, number>>>([]);
  const [portfolioInvestedAmounts, setPortfolioInvestedAmounts] = useState<Array<Record<string, number>>>([]);
  const [portfolioGain, setPortfolioGain] = useState<Array<Record<string, number>>>([]);
  const [twr, setTwr] = useState<Array<Record<string, number>>>([]);
  const [cagr, setCagr] = useState<Record<string, Record<string, number | null>>>({});
  const [fees, setFees] = useState<Array<Record<string, number>>>([]);
  const [dividendEarn, setDividendEarn] = useState<Array<Record<string, number>>>([]);
  const [dividendYield, setDividendYield] = useState<Record<string, number>>({});

  useEffect(() => {
    if (!selectedPortfolio?.id) return;

    const fetchData = async () => {
      try {
        const res = await api.get(`/api/portfolio-performance/${selectedPortfolio.id}/`, {
          params: {
            fields:
              "portfolio_valuation,portfolio_twr,portfolio_cagr,portfolio_fees,portfolio_dividend_earn,portfolio_dividend_yield,portfolio_invested_amounts,portfolio_gain",
          },
        });
        const data = res.data;

        setPortfolioValuation(data.portfolio_valuation || []);
        setTwr(data.portfolio_twr || []);
        setCagr(data.portfolio_cagr || {});
        setFees(data.portfolio_fees || []);
        setDividendEarn(data.portfolio_dividend_earn || {});
        setDividendYield(data.portfolio_dividend_yield || {});
        setPortfolioInvestedAmounts(data.portfolio_invested_amounts || []);
        setPortfolioGain(data.portfolio_gain || []);
      } catch (error) {
        console.error("Error fetching performance data:", error);
      }
    };

    fetchData();
  }, [selectedPortfolio]);

  const twrValue = twr.at(-1)?.[portfolioGlobalName];
  const rawTwr: number | null = typeof twrValue === "number" ? twrValue : null;
  const formattedTwr = rawTwr !== null ? rawTwr.toFixed(2) : "";

  const cagrValue = cagr?.[portfolioGlobalName]?.["all"];
  const rawCagr = typeof cagrValue === "number" ? cagrValue : null;
  const formattedCagr = rawCagr !== null ? rawCagr.toFixed(2) : "";

  const lastFees = fees?.at(-1)?.[portfolioGlobalName] ?? 0;
  // const rawDividendEarn = dividendEarn?.at(-1)?.[portfolioGlobalName] ?? 0;
  const rawDividendYield = dividendYield?.[portfolioGlobalName] ?? 0;

  return (
    <div className="grid grid-cols-1 gap-4 *:data-[slot=card]:bg-gradient-to-t *:data-[slot=card]:shadow-xs @xl/main:grid-cols-2 @5xl/main:grid-cols-3">
      {/* Valeur du portefeuille */}
      <Card className="@container/card">
        <CardHeader>
          <CardDescription>Valeur du portefeuille</CardDescription>
          <CardTitle className="text-2xl font-semibold tabular-nums @[250px]/card:text-3xl">
            {portfolioValuation?.at(-1)?.[portfolioGlobalName]?.toFixed(2) ?? "0.00"}€
          </CardTitle>
        </CardHeader>
        <CardFooter className="flex-col items-start gap-1.5 text-sm">
          <div className="line-clamp-1 flex gap-2 font-medium">
            <Badge
              variant="outline"
              className={`border ${
                rawTwr !== null && rawTwr > 0
                  ? "text-emerald-500 border-emerald-500"
                  : "text-red-500 border-red-500"
              }`}
            >
              {rawTwr !== null && rawTwr > 0 ? <IconTrendingUp /> : <IconTrendingDown />}
              {formattedTwr}%
            </Badge>
            de plus-values latentes
          </div>
          <div className="text-muted-foreground">
            Montant investi : {portfolioInvestedAmounts?.at(-1)?.[portfolioGlobalName] ?? 0} €
          </div>
        </CardFooter>
      </Card>

      {/* Performance */}
      <Card className="@container/card">
        <CardHeader>
          <CardDescription>Performance</CardDescription>
          <CardTitle className="text-2xl font-semibold tabular-nums @[250px]/card:text-3xl">
            {portfolioGain?.at(-1)?.[portfolioGlobalName]?.toFixed(2) ?? "0.00"}€
          </CardTitle>
        </CardHeader>
        <CardFooter className="flex-col items-start gap-1.5 text-sm">
          <div className="line-clamp-1 flex gap-2 font-medium">
            <Badge
              variant="outline"
              className={`border ${
                rawCagr !== null && rawCagr > 0
                  ? "text-emerald-500 border-emerald-500"
                  : "text-red-500 border-red-500"
              }`}
            >
              {rawCagr !== null && rawCagr > 0 ? <IconTrendingUp /> : <IconTrendingDown />}
              {formattedCagr}%
            </Badge>
            CAGR (taux de croissance annualisé)
          </div>
          <div className="text-muted-foreground">
            Les frais s'élèvent à {lastFees} €
          </div>
        </CardFooter>
      </Card>

      {/* Dividendes */}
      <Card className="@container/card">
        <CardHeader>
          <CardDescription>Dividendes</CardDescription>
          <CardTitle className="text-2xl font-semibold tabular-nums @[250px]/card:text-3xl">
            {rawDividendYield.toFixed(2)}%
          </CardTitle>
        </CardHeader>
        <CardFooter className="flex-col items-start gap-1.5 text-sm">
          <div className="line-clamp-1 flex gap-2 font-medium">
            <Badge variant="outline" className="text-blue-500 border-blue-500">
              <IconCash />
              {rawDividendYield.toFixed(2)}%
            </Badge>
            de rendement
          </div>
          <div className="text-muted-foreground">
            Dividendes perçus depuis le début
          </div>
        </CardFooter>
      </Card>
    </div>
  );
}
