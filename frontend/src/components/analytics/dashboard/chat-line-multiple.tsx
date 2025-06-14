"use client";

import { CartesianGrid, Line, LineChart, XAxis } from "recharts";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  ChartConfig,
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart";
import { useEffect, useState } from "react";
import api from "@/api";
import { PortfolioData, portfolioGlobalName } from "@/components/analytics/type";

const chartConfig = {
  desktop: {
    label: portfolioGlobalName,
    color: "var(--chart-1)",
  },
  mobile: {
    label: "S&P 500 DCA",
    color: "var(--chart-2)",
  },
} satisfies ChartConfig;

type ChartLineMultipleProps = {
  title: string;
  height: number;
  performanceData: PortfolioData | undefined;
};

export function ChartLineMultiple({
  title,
  height,
  performanceData,
}: ChartLineMultipleProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-2xl font-bold">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <ChartContainer
          config={chartConfig}
          style={{ height: `${height}px` }}
          className="mx-auto aspect-square w-full"
        >
          <LineChart
            accessibilityLayer
            data={performanceData?.[portfolioGlobalName]?.portfolio_twr ?? []}
            margin={{
              left: 12,
              right: 12,
            }}
          >
            <CartesianGrid vertical={false} />
            <XAxis
              dataKey="date"
              tickLine={false}
              axisLine={false}
              tickMargin={8}
              tickFormatter={(value) => value.slice(0, 3)}
            />
            <ChartTooltip cursor={false} content={<ChartTooltipContent />} />
            <Line
              dataKey={portfolioGlobalName}
              type="monotone"
              stroke="blue"
              strokeWidth={2}
              dot={false}
            />
            <Line
              dataKey="S&P 500 DCA"
              type="monotone"
              stroke="green"
              strokeWidth={2}
              dot={false}
            />
          </LineChart>
        </ChartContainer>
      </CardContent>
    </Card>
  );
}
