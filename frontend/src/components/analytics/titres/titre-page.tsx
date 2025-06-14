import React from "react";

import { StockStatisticsCard } from "@/components/analytics/titres/cards-summary";
import { ChartPieLabelListInteraction } from "@/components/analytics/titres/chart-pie-label-list-interaction";
import { NavBar } from "@/components/analytics/titres/board/navigation-board";
import { ChartBarLabel } from "@/components/analytics/titres/chart-bar-label";

export default function TitresPage({ data }: PortfolioPerformances) {
  return (
    <div className="@container/main flex flex-1 flex-col gap-2">
      <div className="flex flex-col gap-4 py-4 md:gap-6 md:py-6">
        <ChartBarLabel />
        <NavBar />

        <div className="flex w-full gap-4">
          <div className="w-[40%]">
            <ChartPieLabelListInteraction
              title="Répartition"
              height={400}
              size={85}
            />
          </div>
          <div className="w-[60%]">
            <StockStatisticsCard title="Statistiques" height={515} />
          </div>
        </div>
      </div>
    </div>
  );
}
