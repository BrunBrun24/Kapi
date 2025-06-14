import React from "react";

import { BarMonth } from "@/components/analytics/dividends/bar-month";

export default function DividendsPage({ data }: PortfolioPerformances) {
  return (
    <div className="@container/main flex flex-1 flex-col gap-2">
      <div className="flex flex-col gap-4">
        <div className="flex w-full gap-4">
          <div className="w-[50%]">
            <BarMonth title="Par mois" height={500} selectedYear={true} />
          </div>
          <div className="w-[50%]">
            <BarMonth title="Par année" height={500} />
          </div>
        </div>
      </div>
    </div>
  );
}
