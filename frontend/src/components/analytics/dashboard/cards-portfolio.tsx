import { IconTrendingUp, IconCash } from "@tabler/icons-react";
import { Badge } from "@/components/ui/badge";

import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import type { PortfolioCardData, PortfolioPerformances } from "@/components/analytics/type";

export function CardsPortfolio() {
  return (
    <Card className="p-6 border-gray-300">
      <div className="grid grid-cols-4 divide-x divide-gray-300">
        {/* Informations */}
        <div className="px-4 flex flex-col justify-center">
          <CardHeader className="p-0 mb-2">
            <CardTitle className="text-2xl font-bold">IBKR PEA</CardTitle>
          </CardHeader>

          <CardContent className="p-0 space-y-2 text-sm">
            <div>
              <span className="text-gray-400">Depuis le </span>
              <span className="font-semibold text-gray-900">06/04/2022</span>
            </div>
            <div>
              <span className="text-gray-400">Frais : </span>
              <span className="font-semibold text-gray-900">25,1 €</span>
            </div>
            <div>
              <span className="text-gray-400">Solde : </span>
              <span className="font-semibold text-gray-900">12,50 €</span>
            </div>
          </CardContent>
        </div>

        {/* Valeur total */}
        <div className="px-4 flex flex-col justify-center">
          <CardHeader className="p-0 mb-2">
            <CardTitle>Valeur total</CardTitle>
          </CardHeader>

          <CardContent className="p-0 space-y-2 text-sm">
            <div>
              <span className="font-semibold font-bold text-xl text-gray-900">
                34 134,35 €{" "}
              </span>
              <span className="text-gray-400">sur </span>
              <span className="font-semibold text-gray-900">25 800 € </span>
              <span className="text-gray-400">investis</span>
            </div>
            <div>
              <Badge
                variant="outline"
                className="text-emerald-500 border-emerald-500"
              >
                <IconTrendingUp />
                +12.5%
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
                14 000,35 €{" "}
              </span>
              <span className="text-gray-400"> de plus-values latentes</span>
            </div>
            <div>
              <Badge
                variant="outline"
                className="text-emerald-500 border-emerald-500"
              >
                <IconTrendingUp />
                +7.23%
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
                326,05 €{" "}
              </span>
              <span className="text-gray-400">de dividendes perçus</span>
            </div>
            <div>
              <Badge
                variant="outline"
                className="text-blue-500 border-blue-500"
              >
                <IconCash />
                0,24%
              </Badge>
              <span className="text-gray-400"> de rendements</span>
            </div>
          </CardContent>
        </div>
      </div>
    </Card>
  );
}
