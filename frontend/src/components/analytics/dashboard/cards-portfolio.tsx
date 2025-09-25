"use client";

import { useEffect, useState } from "react";
import { IconCash, IconTrendingDown, IconTrendingUp } from "@tabler/icons-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import api from "@/api";
import type { UserPortfolio } from "@/components/analytics/type";

type PortfolioMetrics = {
  valuation: number;
  invested: number;
  gain: number;
  twr: number;
  cagr: number | null;
  fees: number;
  dividendYield: number;
  dividendEarn: number;
  cash: number;
};

export function CardsPortfolio() {
  const [dataPortfolio, setDataPortfolio] = useState<UserPortfolio[]>([]);
  const [metrics, setMetrics] = useState<Record<string, PortfolioMetrics>>({});

  useEffect(() => {
    const fetchPortfolioData = async () => {
      try {
        const res = await api.get<UserPortfolio[]>(
          "api/user/portfolio/utilisateur/"
        );
        setDataPortfolio(res.data);

        for (const portfolio of res.data) {
          const perfRes = await api.get(
            `/api/portfolio-performance/${portfolio.id}/`,
            {
              params: {
                fields:
                  "portfolio_valuation,portfolio_twr,portfolio_cagr,portfolio_fees,portfolio_dividend_yield,portfolio_invested_amounts,portfolio_gain,portfolio_dividend_earn,portfolio_cash",
              },
            }
          );

          const data = perfRes.data;

          setMetrics((prev) => ({
            ...prev,
            [portfolio.name]: {
              valuation: data.portfolio_valuation?.at(-1)?.[portfolio.name] ?? 0,
              invested: data.portfolio_invested_amounts?.at(-1)?.[portfolio.name] ?? 0,
              gain: data.portfolio_gain?.at(-1)?.[portfolio.name] ?? 0,
              twr: data.portfolio_twr?.at(-1)?.[portfolio.name] ?? 0,
              cagr: data.portfolio_cagr?.[portfolio.name]?.all ?? null,
              fees: data.portfolio_fees?.at(-1)?.[portfolio.name] ?? 0,
              dividendYield: data.portfolio_dividend_yield?.[portfolio.name] ?? 0,
              dividendEarn: data.portfolio_dividend_earn?.[portfolio.name] ?? 0,
              cash: data.portfolio_cash?.at(-1)?.[portfolio.name] ?? 0,
            },
          }));
        }
      } catch (error) {
        console.error("Erreur lors de la récupération des données de performance", error);
      }
    };

    fetchPortfolioData();
  }, []);

  const formatNumber = (value?: number | null) =>
    typeof value === "number" ? value.toFixed(2) : "—";

  return (
    <div className="space-y-6">
      {dataPortfolio.map((portfolio) => {
        const m = metrics[portfolio.name];
        if (!m) return null;

        return (
          <Card key={portfolio.name} className="p-6 border-gray-300">
            <div className="grid grid-cols-4 divide-x divide-gray-300">
              {/* Informations */}
              <div className="px-4 flex flex-col justify-center">
                <CardHeader className="p-0 mb-2">
                  <CardTitle className="text-2xl font-bold">{portfolio.name}</CardTitle>
                </CardHeader>
                <CardContent className="p-0 space-y-2 text-sm">
                  <div>
                    <span className="text-gray-400">Depuis le </span>
                    <span className="font-semibold text-gray-900">06/04/2022</span>
                  </div>
                  <div>
                    <span className="text-gray-400">Frais : </span>
                    <span className="font-semibold text-gray-900">{formatNumber(m.fees)} €</span>
                  </div>
                  <div>
                    <span className="text-gray-400">Solde : </span>
                    <span className="font-semibold text-gray-900">{formatNumber(m.cash)} €</span>
                  </div>
                </CardContent>
              </div>

              {/* Valeur totale */}
              <div className="px-4 flex flex-col justify-center">
                <CardHeader className="p-0 mb-2">
                  <CardTitle>Valeur totale</CardTitle>
                </CardHeader>
                <CardContent className="p-0 space-y-2 text-sm">
                  <div>
                    <span className="font-semibold font-bold text-xl text-gray-900">
                      {formatNumber(m.valuation)} €
                    </span>
                    <span className="text-gray-400"> sur </span>
                    <span className="font-semibold text-gray-900">
                      {formatNumber(m.invested)} €
                    </span>
                    <span className="text-gray-400"> investis</span>
                  </div>
                  <div>
                    <Badge
                      variant="outline"
                      className={`border ${
                        m.twr > 0
                          ? "text-emerald-500 border-emerald-500"
                          : "text-red-500 border-red-500"
                      }`}
                    >
                      {m.twr > 0 ? <IconTrendingUp /> : <IconTrendingDown />}
                      {formatNumber(m.twr)}%
                    </Badge>
                    <span className="text-gray-400"> de plus-values latentes</span>
                  </div>
                </CardContent>
              </div>

              {/* Performance */}
              <div className="px-4 flex flex-col justify-center">
                <CardHeader className="p-0 mb-2">
                  <CardTitle>Performance</CardTitle>
                </CardHeader>
                <CardContent className="p-0 space-y-2 text-sm">
                  <div>
                    <span className="font-semibold font-bold text-xl text-emerald-500">
                      {formatNumber(m.gain)} €
                    </span>
                    <span className="text-gray-400"> de plus-values latentes</span>
                  </div>
                  <div>
                    <Badge
                      variant="outline"
                      className={`border ${
                        m.cagr && m.cagr > 0
                          ? "text-emerald-500 border-emerald-500"
                          : "text-red-500 border-red-500"
                      }`}
                    >
                      {m.cagr && m.cagr > 0 ? <IconTrendingUp /> : <IconTrendingDown />}
                      {formatNumber(m.cagr)}%
                    </Badge>
                    <span className="text-gray-400"> CAGR (taux de croissance annualisé)</span>
                  </div>
                </CardContent>
              </div>

              {/* Dividendes */}
              <div className="px-4 flex flex-col justify-center">
                <CardHeader className="p-0 mb-2">
                  <CardTitle>Dividendes</CardTitle>
                </CardHeader>
                <CardContent className="p-0 space-y-2 text-sm">
                  <div>
                    <span className="font-semibold font-bold text-xl text-gray-900">
                      {formatNumber(m.dividendEarn)} €
                    </span>
                    <span className="text-gray-400"> de dividendes perçus</span>
                  </div>
                  <div>
                    <Badge variant="outline" className="text-blue-500 border-blue-500">
                      <IconCash />
                      {formatNumber(m.dividendYield)}%
                    </Badge>
                    <span className="text-gray-400"> de rendement</span>
                  </div>
                </CardContent>
              </div>
            </div>
          </Card>
        );
      })}
    </div>
  );
}
