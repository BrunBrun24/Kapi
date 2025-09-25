import { ChartLineMultipleInteraction } from "@/components/analytics/chart/chat-line-multiple-interaction";
import { ChartBarNegativeInteraction } from "@/components/analytics/performance/chart-bar-negative-interaction";
import type { SelectedPortfolio } from "@/components/analytics/type";

export default function PerformancePage({
  selectedPortfolio,
}: SelectedPortfolio) {
  return (
    <div className="flex flex-col gap-4 py-4 md:gap-6 md:py-6">
      <ChartLineMultipleInteraction
        title="Performance"
        height={500}
        selectedPortfolio={selectedPortfolio}
      />

      <ChartBarNegativeInteraction
        title="Dynamique des rendements de portefeuille"
        height={500}
        selectedPortfolio={selectedPortfolio}
      />
    </div>
  );
}
