"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  LabelList,
  ReferenceLine,
  XAxis,
  YAxis,
} from "recharts";
import {
  formSchemaYearPortfolioBenchmark,
  FormValuesYearPortfolioBenchmark,
} from "@/components/analytics/performance/type";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  ChartConfig,
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart";
import { FormProvider, useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { FormYearPortfolioBenchmark } from "@/components/analytics/performance/form-chart-bar-negative-interaction";

const chartData = [
  { month: "Jan", percentage: 8 },
  { month: "Feb", percentage: 2 },
  { month: "Mar", percentage: -4.35 },
  { month: "Apr", percentage: 7 },
  { month: "May", percentage: -5 },
  { month: "Jun", percentage: 1.2 },
  { month: "Jul", percentage: -0.5 },
  { month: "Aug", percentage: -0.2 },
  { month: "Sept", percentage: 1.43 },
  { month: "Oct", percentage: 6 },
  { month: "Nov", percentage: -2.58 },
  { month: "Dec", percentage: 12 },
];

const chartConfig = {
  percentage: {
    label: "Percentage",
  },
} satisfies ChartConfig;

function renderCustomLabel({
  x,
  y,
  width,
  value,
}: {
  x?: string | number;
  y?: string | number;
  width?: string | number;
  value?: string | number;
}) {
  if (x == null || y == null || width == null || value == null) {
    return null;
  }

  const parsedX = typeof x === "string" ? parseFloat(x) : x;
  const parsedY = typeof y === "string" ? parseFloat(y) : y;
  const parsedWidth = typeof width === "string" ? parseFloat(width) : width;
  const parsedValue = typeof value === "string" ? parseFloat(value) : value;

  if (
    isNaN(parsedX) ||
    isNaN(parsedY) ||
    isNaN(parsedWidth) ||
    isNaN(parsedValue)
  ) {
    return null;
  }

  const isPositive = parsedValue >= 0;
  const offsetY = isPositive ? -10 : 20;
  const color = isPositive ? "rgb(92,213,172)" : "rgb(239,98,98)";

  return (
    <text
      x={parsedX + parsedWidth / 2}
      y={parsedY + offsetY}
      textAnchor="middle"
      fontSize={14}
      fontWeight="bold"
      fill={color}
    >
      {parsedValue}%
    </text>
  );
}

type ChartBarNegativeInteractionProps = {
  title: string;
  height: number;
};

export function ChartBarNegativeInteraction({
  title,
  height,
}: ChartBarNegativeInteractionProps) {
  const form = useForm<FormValuesYearPortfolioBenchmark>({
    resolver: zodResolver(formSchemaYearPortfolioBenchmark),
    defaultValues: {
      year: "12m",
      portfolio: "all",
      benchmark: "sp500",
    },
  });
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between flex-wrap gap-4">
          <CardTitle className="text-2xl font-bold">{title}</CardTitle>
          <FormProvider {...form}>
            <FormYearPortfolioBenchmark />
          </FormProvider>
        </div>
      </CardHeader>
      <CardContent>
        <ChartContainer
          config={chartConfig}
          style={{ height: `${height}px` }}
          className="w-full aspect-auto"
        >
          {/* Ton BarChart ici */}
          <BarChart
            data={chartData}
            margin={{ top: 20, right: 30, left: 20, bottom: 20 }}
          >
            <CartesianGrid vertical={false} strokeDasharray="3 3" />
            <XAxis dataKey="month" />
            <YAxis
              domain={["dataMin - 5", "dataMax + 5"]} // marge en haut et en bas
              padding={{ top: 10, bottom: 10 }}
            />

            <ReferenceLine y={0} stroke="#ccc" strokeWidth={1} />
            <ChartTooltip
              cursor={{ fill: "transparent" }}
              content={<ChartTooltipContent hideLabel hideIndicator />}
            />
            <Bar dataKey="percentage">
              <LabelList dataKey="percentage" content={renderCustomLabel} />

              {chartData.map((item) => (
                <Cell
                  key={item.month}
                  fill={
                    item.percentage < 0 ? "rgb(239,98,98)" : "rgb(92,213,172)"
                  }
                />
              ))}
            </Bar>
          </BarChart>
        </ChartContainer>
      </CardContent>
    </Card>
  );
}
