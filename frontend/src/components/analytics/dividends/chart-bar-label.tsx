"use client";

import {
  ChartConfig,
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart";
import { Bar, BarChart, CartesianGrid, LabelList, XAxis } from "recharts";

const chartConfig = {
  dividends: {
    label: "Dividendes",
    color: "var(--chart-1)",
  },
} satisfies ChartConfig;

type ChartBarLabelProps = {
  chartData: Record<string, number>;
  height: number;
};

export function ChartBarLabel({ chartData, height }: ChartBarLabelProps) {
  // Transformation générique
  const data = Object.entries(chartData).map(([key, value]) => ({
    label:
      key.length === 4
        ? key // si 4 chiffres → année
        : new Date(0, Number(key) - 1).toLocaleString("en", { month: "long" }),
    dividends: value,
  }));

  return (
    <ChartContainer
      config={chartConfig}
      style={{ height }}
      className="mx-auto w-full"
    >
      <BarChart accessibilityLayer data={data} margin={{ top: 20 }}>
        <CartesianGrid vertical={false} />
        <XAxis
          dataKey="label"
          tickLine={false}
          tickMargin={10}
          axisLine={false}
          tickFormatter={(value) =>
            value.length === 4 ? value : value.slice(0, 3)
          }
        />

        <ChartTooltip
          cursor={false}
          content={<ChartTooltipContent hideLabel />}
        />
        <Bar dataKey="dividends" fill="#55A4FD" radius={8}>
          <LabelList
            position="top"
            offset={12}
            className="fill-foreground"
            fontSize={12}
            formatter={(value: number) => `${value.toFixed(2)} €`}
          />
        </Bar>
      </BarChart>
    </ChartContainer>
  );
}
