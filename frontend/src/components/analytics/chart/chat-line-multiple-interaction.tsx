"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { FormProvider, useForm } from "react-hook-form";
import { CartesianGrid, Line, LineChart, XAxis } from "recharts";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  ChartConfig,
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart";

import { FormDatePortfolioBenchmark } from "@/components/analytics/chart/form-chart-line-multiple-interaction";
import {
  formSchemaDatePortfolioBenchmark,
  FormValuesDatePortfolioBenchmark,
} from "@/components/analytics/performance/type";
import type { PortfolioCardData, PortfolioPerformances } from "@/components/analytics/type";

const chartConfig = {
  desktop: {
    label: "Desktop",
    color: "var(--chart-1)",
  },
  mobile: {
    label: "Mobile",
    color: "var(--chart-2)",
  },
} satisfies ChartConfig;

type ChartLineMultipleInteractionProps = {
  title: string;
  height: number;
  performanceData: PortfolioPerformances | undefined;
  portfolioId: number | undefined;
};

export function ChartLineMultipleInteraction({
  title,
  height,
  performanceData,
  portfolioId,
}: ChartLineMultipleInteractionProps) {
  const form = useForm<FormValuesDatePortfolioBenchmark>({
    resolver: zodResolver(formSchemaDatePortfolioBenchmark),
    defaultValues: {
      date: new Date(),
      portfolio: "My Portfolio",
      benchmark: "sp500",
    },
  });

  console.log(portfolioId);

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between flex-wrap gap-4">
          <CardTitle className="text-2xl font-bold">{title}</CardTitle>
          <FormProvider {...form}>
            <FormDatePortfolioBenchmark />
          </FormProvider>
        </div>
      </CardHeader>

      <CardContent>
        <ChartContainer
          config={chartConfig}
          style={{ height: `${height}px` }}
          className="mx-auto aspect-square w-full"
        >
          <LineChart
            accessibilityLayer
            data={performanceData?.portfolio_twr ?? []}
            margin={{
              left: 12,
              right: 12,
            }}
          >
            <CartesianGrid vertical={false} />
            <XAxis
              dataKey="month"
              tickLine={false}
              axisLine={false}
              tickMargin={8}
              tickFormatter={(value) => value.slice(0, 3)}
            />
            <ChartTooltip cursor={false} content={<ChartTooltipContent />} />
            <Line
              dataKey={portfolioId}
              type="monotone"
              stroke="var(--color-desktop)"
              strokeWidth={2}
              dot={false}
            />
            <Line
              dataKey="S&P 500 DCA"
              type="monotone"
              stroke="var(--color-mobile)"
              strokeWidth={2}
              dot={false}
            />
          </LineChart>
        </ChartContainer>
      </CardContent>
    </Card>
  );
}
