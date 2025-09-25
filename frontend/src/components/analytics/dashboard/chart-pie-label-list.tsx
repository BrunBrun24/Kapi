"use client";

import api from "@/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart";
import { useEffect, useState } from "react";
import { Pie, PieChart } from "recharts";

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

type ChartPieLabelListProps = {
  title: string;
  height: number;
  size: number;
};

type ChartDataItem = {
  portfolio: string;
  repartition: number;
  fill: string;
};

export function ChartPieLabelList({
  title,
  height,
  size,
}: ChartPieLabelListProps) {
  const [chartData, setChartData] = useState<ChartDataItem[] | null>(null);
  const [chartConfig, setChartConfig] = useState<Record<string, any> | null>(
    null
  );

  useEffect(() => {
    const getUserPortfolioData = async () => {
      try {
        const res = await api.get(
          "/api/portfolio-performance/portfolio/repartition/"
        );
        const data = res.data;
        setChartData(data[0]);
        setChartConfig(data[1]);
      } catch (error) {
        console.error(
          "Erreur lors de la récupération des portefeuilles",
          error
        );
      }
    };

    getUserPortfolioData();
  }, []);

  if (!chartData || !chartConfig) {
    return (
      <Card className="flex flex-col items-center justify-center">
        <CardHeader className="items-center pb-0">
          <CardTitle className="text-2xl font-bold">{title}</CardTitle>
        </CardHeader>
        <CardContent className="flex-1 pb-0 flex items-center justify-center">
          <p className="text-sm text-muted-foreground">
            Chargement en cours...
          </p>
        </CardContent>
      </Card>
    );
  }

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
