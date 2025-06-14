"use client";

import { Pie, PieChart } from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  ChartConfig,
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart";
import { FormProvider, useForm } from "react-hook-form";

import { FormType } from "@/components/analytics/titres/form-chart-line-multiple-interaction";
import { zodResolver } from "@hookform/resolvers/zod";
import {
  formSchemaType,
  FormValuesType,
} from "@/components/analytics/performance/type";

const chartData = [
  { browser: "Chrome", visitors: 65, fill: "var(--chart-1)" },
  { browser: "Safari", visitors: 15, fill: "var(--chart-2)" },
  { browser: "Firefox", visitors: 14, fill: "var(--chart-3)" },
  { browser: "Edge", visitors: 5, fill: "var(--chart-4)" },
  { browser: "Other", visitors: 1, fill: "var(--chart-5)" },
];

const chartConfig = {
  visitors: {
    label: "Visitors",
  },
  Chrome: {
    label: "Chrome",
    color: "var(--chart-1)",
  },
  Safari: {
    label: "Safari",
    color: "var(--chart-2)",
  },
  Firefox: {
    label: "Firefox",
    color: "var(--chart-3)",
  },
  Edge: {
    label: "Edge",
    color: "var(--chart-4)",
  },
  Other: {
    label: "Other",
    color: "var(--chart-5)",
  },
} satisfies ChartConfig;

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
      {payload.browser}
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

  if (payload.visitors < 5) return null;

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
      {payload.visitors}%
    </text>
  );
}

type ChartPieLabelListInteractionProps = {
  title: string;
  height: number;
  size: number;
};

export function ChartPieLabelListInteraction({
  title,
  height,
  size,
}: ChartPieLabelListInteractionProps) {
  const form = useForm<FormValuesType>({
    resolver: zodResolver(formSchemaType),
    defaultValues: {
      type: "all",
    },
  });
  return (
    <Card className="flex flex-col">
      <CardHeader>
        <div className="flex items-center justify-between flex-wrap gap-4">
          <CardTitle className="text-2xl font-bold">{title}</CardTitle>
          <FormProvider {...form}>
            <FormType />
          </FormProvider>
        </div>
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
              dataKey="visitors"
              nameKey="browser"
              outerRadius={size + "%"}
              labelLine={false}
              label={renderBrowserLabel}
            />
            <Pie
              data={chartData}
              dataKey="visitors"
              nameKey="browser"
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
