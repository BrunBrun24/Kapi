import React from "react";

import { SelectedPortfolio } from "../type";
import { GenericBarChart } from "@/components/analytics/hooks/generic-bar-chart";

export default function InvestissementsPage({
  selectedPortfolio,
}: SelectedPortfolio) {
  return (
    <div className="@container/main flex flex-1 flex-col gap-2">
      <div className="flex flex-col gap-4">
        <div className="flex w-full gap-4">
          <div className="w-[100%]">
            <GenericBarChart
              selectedPortfolio={selectedPortfolio}
              height={500}
              title="Investissement"
              dataType="investissements"
            />
          </div>
        </div>
      </div>
    </div>
  );
}
