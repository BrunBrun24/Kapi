"use client";

import { Bar, BarChart, CartesianGrid, LabelList, XAxis } from "recharts";

import {
  ChartConfig,
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart";

const chartData = [
  { month: "January", desktop: 5 },
  { month: "February", desktop: 1 },
  { month: "March", desktop: 13 },
  { month: "April", desktop: 42 },
  { month: "May", desktop: 15 },
  { month: "June", desktop: 6 },
  { month: "July", desktop: 52 },
  { month: "Auguste", desktop: 43 },
  { month: "September", desktop: 21 },
  { month: "October", desktop: 11 },
  { month: "November", desktop: 9 },
  { month: "December", desktop: 32 },
];

const chartConfig = {
  desktop: {
    label: "Desktop",
    color: "var(--chart-1)",
  },
} satisfies ChartConfig;

type ChartBarLabelProps = {
  height: number;
};

export function ChartBarLabel({ height }: ChartBarLabelProps) {
  return (
    <ChartContainer
      config={chartConfig}
      style={{ height }}
      className="mx-auto w-full"
    >
      <BarChart
        accessibilityLayer
        data={chartData}
        margin={{
          top: 20,
        }}
      >
        <CartesianGrid vertical={false} />
        <XAxis
          dataKey="month"
          tickLine={false}
          tickMargin={10}
          axisLine={false}
          tickFormatter={(value) => value.slice(0, 3)}
        />
        <ChartTooltip
          cursor={false}
          content={<ChartTooltipContent hideLabel />}
        />
        <Bar dataKey="desktop" fill="var(--color-desktop)" radius={8}>
          <LabelList
            position="top"
            offset={12}
            className="fill-foreground"
            fontSize={12}
          />
        </Bar>
      </BarChart>
    </ChartContainer>
  );
}
