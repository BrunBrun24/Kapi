"use client";

import { Bar, BarChart, XAxis } from "recharts";

import {
  ChartConfig,
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart";

// ✅ Données mensuelles de dividendes
const chartData = [
  { month: "Jan", AAPL: 120, MSFT: 150 },
  { month: "Feb", AAPL: 95, MSFT: 130 },
  { month: "Mar", AAPL: 110, MSFT: 145 },
  { month: "Apr", AAPL: 100, MSFT: 160 },
  { month: "May", AAPL: 105, MSFT: 135 },
  { month: "Jun", AAPL: 115, MSFT: 155 },
];

// ✅ Configuration du graphique
const chartConfig = {
  AAPL: {
    label: "Apple (AAPL)",
    color: "var(--chart-1)",
  },
  MSFT: {
    label: "Microsoft (MSFT)",
    color: "var(--chart-2)",
  },
} satisfies ChartConfig;

type ChartTooltipAdvancedProps = {
  height: number;
};

export function ChartTooltipAdvanced({ height }: ChartTooltipAdvancedProps) {
  return (
    <ChartContainer
      config={chartConfig}
      style={{ height }}
      className="mx-auto w-full"
    >
      <BarChart accessibilityLayer data={chartData}>
        <XAxis
          dataKey="month"
          tickLine={false}
          tickMargin={10}
          axisLine={false}
        />
        <Bar
          dataKey="AAPL"
          stackId="a"
          fill="var(--color-AAPL)"
          radius={[0, 0, 4, 4]}
        />
        <Bar
          dataKey="MSFT"
          stackId="a"
          fill="var(--color-MSFT)"
          radius={[4, 4, 0, 0]}
        />
        <ChartTooltip
          content={
            <ChartTooltipContent
              hideLabel
              className="w-[180px]"
              formatter={(value, name, item, index) => (
                <>
                  <div
                    className="h-2.5 w-2.5 shrink-0 rounded-[2px] bg-(--color-bg)"
                    style={
                      {
                        "--color-bg": `var(--color-${name})`,
                      } as React.CSSProperties
                    }
                  />
                  {chartConfig[name as keyof typeof chartConfig]?.label || name}
                  <div className="text-foreground ml-auto flex items-baseline gap-0.5 font-mono font-medium tabular-nums">
                    {value}
                    <span className="text-muted-foreground font-normal">
                      €
                    </span>
                  </div>
                  {index === 1 && (
                    <div className="text-foreground mt-1.5 flex basis-full items-center border-t pt-1.5 text-xs font-medium">
                      Total
                      <div className="text-foreground ml-auto flex items-baseline gap-0.5 font-mono font-medium tabular-nums">
                        {item.payload.AAPL + item.payload.MSFT}
                        <span className="text-muted-foreground font-normal">
                          €
                        </span>
                      </div>
                    </div>
                  )}
                </>
              )}
            />
          }
          cursor={false}
        />
      </BarChart>
    </ChartContainer>
  );
}
