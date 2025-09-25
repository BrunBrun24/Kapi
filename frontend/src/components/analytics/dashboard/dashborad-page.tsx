import { CardsPortfolio } from "@/components/analytics/dashboard/cards-portfolio";
import { CardsSummary } from "@/components/analytics/dashboard/cards-summary";
import { ChartPieLabelList } from "@/components/analytics/dashboard/chart-pie-label-list";
import { ChartLineMultiple } from "@/components/analytics/dashboard/chat-line-multiple";
import type { SelectedPortfolio } from "@/components/analytics/type";

export default function DashboardPage({
  selectedPortfolio,
}: SelectedPortfolio) {
  return (
    <div className="@container/main flex flex-1 flex-col gap-2">
      <div className="flex flex-col gap-4 py-4 md:gap-6 md:py-6">
        <CardsSummary selectedPortfolio={selectedPortfolio} />

        {/* Flex row 70% / 30% split */}
        <div className="flex w-full gap-4">
          <div className="w-[70%]">
            <ChartLineMultiple
              title="Performance"
              height={320}
              selectedPortfolio={selectedPortfolio}
            />
          </div>
          <div className="w-[30%]">
            <ChartPieLabelList title="Répartition" height={320} size={85} />
          </div>
        </div>

        <CardsPortfolio />
      </div>
    </div>
  );
}
