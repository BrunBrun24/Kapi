import {
  IconCash,
  IconTrendingDown,
  IconTrendingUp,
} from "@tabler/icons-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";

import { useEffect, useState } from "react";
import api from "@/api";
import type {
  PortfolioPerformances,
  UserPortfolio,
} from "@/components/analytics/type";

type CardsPortfolioProps = {
  selectedPortfolio?: UserPortfolio;
};

export function CardsPortfolio({ selectedPortfolio }: CardsPortfolioProps) {
  const [dataPortfolio, setDataPortfolio] = useState<
    UserPortfolio[] | undefined
  >();

  const [portfolioValuation, setPortfolioValuation] = useState<
    Record<string, number>
  >({});
  const [portfolioInvestedAmounts, setPortfolioInvestedAmounts] = useState<
    Record<string, number>
  >({});
  const [portfolioGain, setPortfolioGain] = useState<Record<string, number>>(
    {}
  );
  const [twr, setTwr] = useState<Record<string, number>>({});
  const [cagr, setCagr] = useState<Record<string, number | null>>({});
  const [fees, setFees] = useState<Record<string, number>>({});
  const [dividendYield, setDividendYield] = useState<Record<string, number>>(
    {}
  );
  const [dividendEarn, setDividendEarn] = useState<Record<string, number>>({});
  const [cash, setCash] = useState<Record<string, number>>({});

  useEffect(() => {
    const getUserPortfolioData = async () => {
      try {
        const res = await api.get("api/user/portfolio/utilisateur/");
        const fetchedData = res.data as UserPortfolio[];
        setDataPortfolio(fetchedData);

        // Fetch performances for each portfolio
        for (const portfolio of fetchedData) {
          const res = await api.get(
            `/api/portfolio-performance/${portfolio.id}/`,
            {
              params: {
                fields:
                  "portfolio_valuation,portfolio_twr,portfolio_cagr,portfolio_fees,portfolio_dividend_yield,portfolio_invested_amounts,portfolio_gain,portfolio_dividend_earn,portfolio_cash",
              },
            }
          );
          const data = res.data;

          setPortfolioValuation((prev) => ({
            ...prev,
            [portfolio.name]:
              data.portfolio_valuation?.at(-1)?.[portfolio.name] ?? 0,
          }));
          setPortfolioInvestedAmounts((prev) => ({
            ...prev,
            [portfolio.name]:
              data.portfolio_invested_amounts?.at(-1)?.[portfolio.name] ?? 0,
          }));
          setPortfolioGain((prev) => ({
            ...prev,
            [portfolio.name]:
              data.portfolio_gain?.at(-1)?.[portfolio.name] ?? 0,
          }));
          setTwr((prev) => ({
            ...prev,
            [portfolio.name]: data.portfolio_twr?.at(-1)?.[portfolio.name] ?? 0,
          }));
          setCagr((prev) => ({
            ...prev,
            [portfolio.name]:
              data.portfolio_cagr?.[portfolio.name]?.all ?? null,
          }));
          setFees((prev) => ({
            ...prev,
            [portfolio.name]:
              data.portfolio_fees?.at(-1)?.[portfolio.name] ?? 0,
          }));
          setDividendYield((prev) => ({
            ...prev,
            [portfolio.name]:
              data.portfolio_dividend_yield?.[portfolio.name] ?? 0,
          }));
          setDividendEarn((prev) => ({
            ...prev,
            [portfolio.name]:
              data.portfolio_dividend_earn?.[portfolio.name] ?? 0,
          }));
          setCash((prev) => ({
            ...prev,
            [portfolio.name]:
              data.portfolio_cash?.at(-1)?.[portfolio.name] ?? 0,
          }));
        }
      } catch (error) {
        console.error(
          "Erreur lors de la récupération des données de performance",
          error
        );
      }
    };

    getUserPortfolioData();
  }, []);

  return (
    <div className="space-y-6">
      {dataPortfolio?.map((portfolio) => {
        const name = portfolio.name;

        const rawCagr = cagr[name] ?? null;
        const formattedCagr =
          typeof rawCagr === "number" ? rawCagr.toFixed(2) : "—";

        const rawTwr = twr[name];
        const formattedTwr =
          typeof rawTwr === "number" ? rawTwr.toFixed(2) : "—";

        const formattedFees =
          typeof fees[name] === "number" ? fees[name].toFixed(2) : "—";
        const formattedDividendYield =
          typeof dividendYield[name] === "number"
            ? dividendYield[name].toFixed(2)
            : "—";
        const formattedDividendEarn =
          typeof dividendEarn[name] === "number"
            ? dividendEarn[name].toFixed(2)
            : "—";
        const formattedCash =
          typeof cash[name] === "number" ? cash[name].toFixed(2) : "—";

        const formatNumber = (value?: number) =>
          typeof value === "number" ? value.toFixed(2) : "—";

        const valuation = formatNumber(portfolioValuation[name]);
        const invested = formatNumber(portfolioInvestedAmounts[name]);
        const gain = formatNumber(portfolioGain[name]);

        return (
          <Card key={portfolio.name} className="p-6 border-gray-300">
            <div className="grid grid-cols-4 divide-x divide-gray-300">
              {/* Informations */}
              <div className="px-4 flex flex-col justify-center">
                <CardHeader className="p-0 mb-2">
                  <CardTitle className="text-2xl font-bold">
                    {portfolio.name}
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-0 space-y-2 text-sm">
                  <div>
                    <span className="text-gray-400">Depuis le </span>
                    <span className="font-semibold text-gray-900">
                      06/04/2022
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-400">Frais : </span>
                    <span className="font-semibold text-gray-900">
                      {formattedFees} €
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-400">Solde : </span>
                    <span className="font-semibold text-gray-900">
                      {formattedCash} €
                    </span>
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
                      {valuation} €
                    </span>
                    <span className="text-gray-400"> sur </span>
                    <span className="font-semibold text-gray-900">
                      {invested} €
                    </span>
                    <span className="text-gray-400"> investis</span>
                  </div>
                  <div>
                    <Badge
                      variant="outline"
                      className={`border ${
                        rawTwr !== null && rawTwr > 0
                          ? "text-emerald-500 border-emerald-500"
                          : "text-red-500 border-red-500"
                      }`}
                    >
                      {rawTwr !== null && rawTwr > 0 ? (
                        <IconTrendingUp />
                      ) : (
                        <IconTrendingDown />
                      )}
                      {formattedTwr}%
                    </Badge>
                    <span className="text-gray-400">
                      {" "}
                      de plus-values latentes
                    </span>
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
                      {gain} €
                    </span>
                    <span className="text-gray-400">
                      {" "}
                      de plus-values latentes
                    </span>
                  </div>
                  <div>
                    <Badge
                      variant="outline"
                      className={`border ${
                        rawCagr !== null && rawCagr > 0
                          ? "text-emerald-500 border-emerald-500"
                          : "text-red-500 border-red-500"
                      }`}
                    >
                      {rawCagr !== null && rawCagr > 0 ? (
                        <IconTrendingUp />
                      ) : (
                        <IconTrendingDown />
                      )}
                      {formattedCagr}%
                    </Badge>
                    <span className="text-gray-400">
                      {" "}
                      CAGR (taux de croissance annualisé)
                    </span>
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
                      {formattedDividendEarn} €
                    </span>
                    <span className="text-gray-400"> de dividendes perçus</span>
                  </div>
                  <div>
                    <Badge
                      variant="outline"
                      className="text-blue-500 border-blue-500"
                    >
                      <IconCash />
                      {formattedDividendYield}%
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
