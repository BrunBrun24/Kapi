"use client";

import { Pie, PieChart } from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  ChartConfig,
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart";
import {
  portfolioGlobalName,
  type PortfolioData
} from "@/components/analytics/type";

// Fonction pour afficher les noms des navigateurs à l'extérieur
function renderBrowserLabel({
  cx = 0,
  cy = 0,
  midAngle = 0,
  outerRadius = 0,
  payload,
}: any) {
  const RADIAN = Math.PI / 180;
  const radius = Number(outerRadius) + 20;
  const x = Number(cx) + radius * Math.cos(-midAngle * RADIAN);
  const y = Number(cy) + radius * Math.sin(-midAngle * RADIAN);

  return (
    <text
      x={x}
      y={y}
      fill="#333"
      textAnchor={x > cx ? "start" : "end"}
      dominantBaseline="central"
      fontSize={12}
    >
      {payload.portfolio}
    </text>
  );
}

// Fonction pour afficher le nombre de visiteurs à l'intérieur
function renderVisitorCount({
  cx = 0,
  cy = 0,
  midAngle = 0,
  innerRadius = 0,
  outerRadius = 0,
  payload,
}: any) {
  const RADIAN = Math.PI / 180;
  const radius =
    Number(innerRadius) + (Number(outerRadius) - Number(innerRadius)) / 2;
  const x = Number(cx) + radius * Math.cos(-midAngle * RADIAN);
  const y = Number(cy) + radius * Math.sin(-midAngle * RADIAN);

  if (payload.repartition < 5) return null;

  return (
    <text
      x={x}
      y={y}
      fill="#fff"
      textAnchor="middle"
      dominantBaseline="central"
      fontSize={12}
      fontWeight="bold"
    >
      {payload.repartition}%
    </text>
  );
}

type ChartDataItem = {
  portfolio: string;
  repartition: number;
  fill: string;
};

type ChartConfigItem = {
  label: string;
  color: string;
};

type ChartConfig = {
  repartition: { label: string };
  [key: string]: ChartConfigItem | { label: string };
};

function buildRepartitionChart(
  performanceData: PortfolioData | undefined
): ChartDataItem[] | undefined {
  if (!performanceData) return;

  const investedPerPortfolio: Record<string, number> = {};

  const grossPriceArray = performanceData[portfolioGlobalName]?.gross_price_by_ticker;
  if (!grossPriceArray) return;

  // On récupère la ligne correspondant à "portfolioGlobal"
  const portfolioGlobalData = grossPriceArray.find(([name]) => name === portfolioGlobalName);
  if (!portfolioGlobalData) return;

  const entries = portfolioGlobalData[1];
  if (!entries || entries.length === 0) return;

  const lastEntryMain = entries.at(-1);

  const totalValue = Object.entries(lastEntryMain).reduce((acc, [key, val]) => {
    if (key === "date" || typeof val !== "number") return acc;
    return acc + val;
  }, 0);

  // On parcourt tous les portefeuilles SAUF le portefeuille principal
  for (const [portfolioName, portfolioData] of Object.entries(performanceData)) {
    if (portfolioName === portfolioGlobalName) continue;

    const entries = portfolioData?.gross_price_by_ticker[0];
    if (!entries || entries.length === 0) continue;

    const lastEntry = entries.at(-1).at(-1);
    if (!lastEntry) continue;

    const value = Object.entries(lastEntry).reduce((acc, [key, val]) => {
      if (key === "date" || typeof val !== "number") return acc;
      return acc + val;
    }, 0);

    investedPerPortfolio[portfolioName] = value;
  }

  // Construction du chartData pour tous les portefeuilles hors portefeuille principal
  const chartData: ChartDataItem[] = Object.entries(investedPerPortfolio).map(
    ([portfolio, value], index) => ({
      portfolio,
      repartition:
        totalValue === 0 ? 0 : Number(((value / totalValue) * 100).toFixed(2)),
      fill: `var(--chart-${index + 1})`,
    })
  );

  return chartData;
}

function buildChartConfig(chartData: ChartDataItem[]): ChartConfig {
  const config: ChartConfig = {
    repartition: {
      label: "Répartition",
    },
  };

  chartData.forEach((item) => {
    config[item.portfolio] = {
      label: item.portfolio,
      color: item.fill,
    };
  });

  return config;
}

type ChartPieLabelListProps = {
  title: string;
  height: number;
  size: number;
  performanceData: PortfolioData | undefined;
};

export function ChartPieLabelList({
  title,
  height,
  size,
  performanceData,
}: ChartPieLabelListProps) {
  const chartData = buildRepartitionChart(performanceData) ?? [];
  const chartConfig = buildChartConfig(chartData);

  return (
    <Card className="flex flex-col">
      <CardHeader className="items-center pb-0">
        <CardTitle className="text-2xl font-bold">{title}</CardTitle>
      </CardHeader>
      <CardContent className="flex-1 pb-0">
        <ChartContainer
          config={chartConfig}
          style={{ height: `${height}px` }}
          className="mx-auto aspect-square w-full"
        >
          <PieChart>
            <ChartTooltip content={<ChartTooltipContent hideLabel />} />
            <Pie
              data={chartData}
              dataKey="repartition"
              nameKey="portfolio"
              outerRadius={size + "%"}
              labelLine={false}
              label={renderBrowserLabel}
            />
            <Pie
              data={chartData}
              dataKey="repartition"
              nameKey="portfolio"
              outerRadius={size + "%"}
              fill="transparent"
              label={renderVisitorCount}
              isAnimationActive={false}
            />
          </PieChart>
        </ChartContainer>
      </CardContent>
    </Card>
  );
}
