"use client";

import { Bar, BarChart, XAxis, LabelList } from "recharts";
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart";

type ChartTooltipAdvancedProps = {
  chartData: { month: string; [ticker: string]: number | string }[];
  height: number;
};

export function ChartTooltipAdvanced({
  chartData,
  height,
}: ChartTooltipAdvancedProps) {
  // ✅ Nettoyer les noms de tickers (remplacer "." par "_")
  const cleanData = chartData.map((entry) => {
    const newEntry: Record<string, number | string> = { month: entry.month };
    Object.entries(entry).forEach(([key, value]) => {
      if (key !== "month") {
        const safeKey = key.replace(/\./g, "_");
        newEntry[safeKey] = value;
      }
    });
    return newEntry;
  });

  // ✅ Extraire tous les tickers (propres)
  const tickers = Array.from(
    new Set(
      cleanData.flatMap((d) => Object.keys(d).filter((k) => k !== "month"))
    )
  );

  // ✅ Ajouter le total pré-calculé pour chaque mois
  const dataWithTotal = cleanData.map((entry) => {
    const total = tickers.reduce((sum, t) => sum + Number(entry[t] || 0), 0);
    return { ...entry, total };
  });

  // ✅ Palette de couleurs (30 couleurs équilibrées)
  const colors = [
    "#E57373",
    "#64B5F6",
    "#FFF176",
    "#81C784",
    "#BA68C8",
    "#FFB74D",
    "#4FC3F7",
    "#F06292",
    "#AED581",
    "#9575CD",
    "#FFF176",
    "#7986CB",
    "#4DB6AC",
    "#FF8A65",
    "#607D8B",
    "#DCE775",
    "#FF7043",
    "#7E57C2",
    "#03A9F4",
    "#FFEB3B",
    "#AED581",
    "#F06292",
    "#64B5F6",
    "#FF5722",
    "#7E57C2",
    "#FFB74D",
    "#81C784",
    "#BA68C8",
    "#4FC3F7",
    "#FF8A65",
  ];

  // ✅ Création du chartConfig avec correspondance propre → original
  const chartConfig: Record<string, { label: string; color: string }> = {};
  tickers.forEach((safeTicker, index) => {
    const originalTicker = chartData
      .flatMap((d) => Object.keys(d))
      .find((k) => k.replace(/\./g, "_") === safeTicker && k !== "month");

    chartConfig[safeTicker] = {
      label: originalTicker || safeTicker,
      color: colors[index % colors.length],
    };
  });

  // Déclarer correctement le type pour chaque entrée
  type DataWithTotalEntry = { total: number } & Record<string, number | string>;

  // ✅ Trier les tickers par somme totale décroissante sur tout le dataset
  const tickerTotals: Record<string, number> = {};
  tickers.forEach((ticker) => {
    tickerTotals[ticker] = (dataWithTotal as DataWithTotalEntry[]).reduce(
      (sum, entry) => sum + Number(entry[ticker] || 0),
      0
    );
  });

  const sortedTickers = [...tickers].sort(
    (a, b) => (tickerTotals[b] || 0) - (tickerTotals[a] || 0)
  );

  return (
    <ChartContainer
      config={chartConfig}
      style={{ height }}
      className="mx-auto w-full"
    >
      <BarChart accessibilityLayer data={dataWithTotal}>
        <XAxis
          dataKey="month"
          tickLine={false}
          tickMargin={10}
          axisLine={false}
        />

        {sortedTickers.map((ticker, index) => {
          const isLast = index === sortedTickers.length - 1;

          return (
            <Bar
              key={ticker}
              dataKey={ticker}
              stackId="a"
              fill={chartConfig[ticker].color}
              radius={
                index === 0
                  ? [0, 0, 4, 4]
                  : index === sortedTickers.length - 1
                  ? [4, 4, 0, 0]
                  : 0
              }
            >
              {/* ✅ Label total au-dessus de la pile */}
              {isLast && (
                <LabelList
                  dataKey="total"
                  position="top"
                  offset={10}
                  formatter={(value: string | number) =>
                    `${Number(value).toFixed(2)} €`
                  }
                  style={{ fontWeight: 600, fill: "#111", fontSize: 12 }}
                />
              )}
            </Bar>
          );
        })}

        <ChartTooltip
          content={
            <ChartTooltipContent
              hideLabel
              className="w-[180px]"
              formatter={(value, name, props, index) => {
                const item = props?.payload as Record<string, number | string>;
                if (!item) return null;

                const monthTickers = Object.keys(item)
                  .filter((key) => key !== "month" && Number(item[key]) > 0)
                  .sort(
                    (a, b) => (tickerTotals[b] || 0) - (tickerTotals[a] || 0)
                  ); // ⚡ ordre décroissant dans tooltip

                const total = monthTickers
                  .reduce((sum, t) => sum + Number(item[t]), 0)
                  .toFixed(2);

                return (
                  <>
                    <div
                      className="h-2.5 w-2.5 shrink-0 rounded-[2px]"
                      style={{ backgroundColor: chartConfig[name]?.color }}
                    />
                    {chartConfig[name]?.label || name}
                    <div className="text-foreground ml-auto flex items-baseline gap-0.5 font-mono font-medium tabular-nums">
                      {value}
                      <span className="text-muted-foreground font-normal">
                        €
                      </span>
                    </div>
                    {index === monthTickers.length - 1 && (
                      <div className="text-foreground mt-1.5 flex basis-full items-center border-t pt-1.5 text-xs font-medium">
                        Total
                        <div className="text-foreground ml-auto flex items-baseline gap-0.5 font-mono font-medium tabular-nums">
                          {total}
                          <span className="text-muted-foreground font-normal">
                            €
                          </span>
                        </div>
                      </div>
                    )}
                  </>
                );
              }}
            />
          }
          cursor={false}
        />
      </BarChart>
    </ChartContainer>
  );
}
