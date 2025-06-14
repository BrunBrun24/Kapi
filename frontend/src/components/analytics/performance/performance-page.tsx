import React from "react";

import { ChartBarNegativeInteraction } from "@/components/analytics/performance/chart-bar-negative-interaction";
import { ChartLineMultipleInteraction } from "@/components/analytics/chart/chat-line-multiple-interaction";
import type { PortfolioCardData, PortfolioPerformances } from "@/components/analytics/type";

export default function PerformancePage({ performanceData, portfolioId }: PortfolioPerformances) {
  return (
    <div className="flex flex-col gap-4 py-4 md:gap-6 md:py-6">
      <ChartLineMultipleInteraction title="Performance" height={500} data={performanceData} portfolioId={portfolioId} />

      <ChartBarNegativeInteraction
        title="Dynamique des rendements de portefeuille"
        height={500}
      />
    </div>
  );
}
