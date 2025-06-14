import React, { useEffect, useState } from "react";

import { CardsPortfolio } from "@/components/analytics/dashboard/cards-portfolio";
import { CardsSummary } from "@/components/analytics/dashboard/cards-summary";
import { ChartLineMultiple } from "@/components/analytics/dashboard/chat-line-multiple";
import { ChartPieLabelList } from "@/components/analytics/dashboard/chart-pie-label-list";
import api from "@/api";
import type { PortfolioCardData, PortfolioPerformances } from "@/components/analytics/type";

function CardsPortfolioData(performanceData: PortfolioPerformances) {
  const portfolioData: PortfolioCardData = {
    data: {
      info: {
        name: "IBKR PEA",
        since: "06/04/2022",
        fees: "25,1 €",
        balance: "12,50 €"
      },
      totalValue: {
        currentValue: "34 134,35 €",
        invested: "25 800 €",
        gainPercentage: "+12.5%"
      },
      performance: {
        capitalGain: "14 000,35 €",
        cagr: "+7.23%"
      },
      dividends: {
        received: "326,05 €",
        yield: "0,24%"
      }
    }
  };

  return portfolioData;
}

export default function DashboardPage({ performanceData }: PortfolioPerformances) {
  return (
    <div className="@container/main flex flex-1 flex-col gap-2">
      <div className="flex flex-col gap-4 py-4 md:gap-6 md:py-6">
        <CardsSummary performanceData={performanceData} />

        {/* Flex row 70% / 30% split */}
        <div className="flex w-full gap-4">
          <div className="w-[70%]">
            <ChartLineMultiple
              title="Performance 18,65%"
              height={320}
              performanceData={performanceData}
            />
          </div>
          <div className="w-[30%]">
            <ChartPieLabelList title="Répartition" height={320} size={85} performanceData={performanceData} />
          </div>
        </div>
        
        <CardsPortfolio />
      </div>
    </div>
  );
}
