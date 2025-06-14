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

import { portfolioGlobalName, type PortfolioPerformances } from "@/components/analytics/type";

export function CardsSummary({ performanceData }: PortfolioPerformances) {
  return (
    <div className="grid grid-cols-1 gap-4 *:data-[slot=card]:bg-gradient-to-t *:data-[slot=card]:shadow-xs @xl/main:grid-cols-2 @5xl/main:grid-cols-3">
      {/* Valeur du portefeuille */}
      <Card className="@container/card">
        <CardHeader>
          <CardDescription>Valeur du portefeuille</CardDescription>
          <CardTitle className="text-2xl font-semibold tabular-nums @[250px]/card:text-3xl">
            {performanceData?.[portfolioGlobalName].bank_balance?.at(-1)?.[portfolioGlobalName]}€
          </CardTitle>
        </CardHeader>
        <CardFooter className="flex-col items-start gap-1.5 text-sm">
          <div className="line-clamp-1 flex gap-2 font-medium">
            <Badge
              variant="outline"
              className="text-emerald-500 border-emerald-500"
            >
              <IconTrendingUp />
              +-{performanceData?.[portfolioGlobalName].portfolio_twr?.at(-1)?.[portfolioGlobalName]}%
            </Badge>
            de plus-values latentes
          </div>
          <div className="text-muted-foreground">Montant investi : 4 108 €</div>
        </CardFooter>
      </Card>

      {/* Performance */}
      <Card className="@container/card">
        <CardHeader>
          <CardDescription>Performance</CardDescription>
          <CardTitle className="text-2xl font-semibold tabular-nums @[250px]/card:text-3xl">
            {performanceData?.[portfolioGlobalName].net_portfolio_price?.at(-1)?.[portfolioGlobalName]}€
          </CardTitle>
        </CardHeader>
        <CardFooter className="flex-col items-start gap-1.5 text-sm">
          <div className="line-clamp-1 flex gap-2 font-medium">
            <Badge variant="outline" className="text-red-500 border-red-500">
              <IconTrendingDown />
              -15,25%
            </Badge>
            CAGR (taux de croissance annualisé)
          </div>
          <div className="text-muted-foreground">
            Les frais s'élèvent à 12,65 €
          </div>
        </CardFooter>
      </Card>

      {/* Dividendes */}
      <Card className="@container/card">
        <CardHeader>
          <CardDescription>Dividendes</CardDescription>
          <CardTitle className="text-2xl font-semibold tabular-nums @[250px]/card:text-3xl">
            45 678€
          </CardTitle>
        </CardHeader>
        <CardFooter className="flex-col items-start gap-1.5 text-sm">
          <div className="line-clamp-1 flex gap-2 font-medium">
            <Badge variant="outline" className="text-blue-500 border-blue-500">
              <IconCash />
              0,24%
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
