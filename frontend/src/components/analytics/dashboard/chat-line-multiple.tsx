"use client";

import {
  CartesianGrid,
  Line,
  LineChart,
  XAxis,
  YAxis, // 👈 Import ajouté
} from "recharts";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  ChartConfig,
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart";
import {
  PortfolioData,
  portfolioGlobalName,
  UserPortfolio,
} from "@/components/analytics/type";
import { useEffect, useState } from "react";
import api from "@/api";

const chartConfig = {
  desktop: {
    label: portfolioGlobalName,
    color: "#55A4FD",
  },
  mobile: {
    label: "S&P 500 DCA",
    color: "#EF8CF8",
  },
} satisfies ChartConfig;

type ChartLineMultipleProps = {
  title: string;
  height: number;
  selectedPortfolio?: UserPortfolio;
};

export function ChartLineMultiple({
  title,
  height,
  selectedPortfolio,
}: ChartLineMultipleProps) {

  const [twr, setTwr] = useState([]);
  
  useEffect(() => {
    if (!selectedPortfolio?.id) return;

    const fetchData = async () => {
      try {
        const res = await api.get(
          `/api/portfolio-performance/${selectedPortfolio.id}/`,
          {
            params: {
              fields: "portfolio_twr",
            },
          }
        );
        const data = res.data;
        setTwr(data.portfolio_twr);
      } catch (error) {
        console.error("Error fetching performance data:", error);
      }
    };

    fetchData();
  }, [selectedPortfolio]);

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
            data={twr}
            margin={{
              left: 24,
              right: 12,
              bottom: 32, // Ajouté pour laisser de la place aux ticks tournés
            }}
          >
            <CartesianGrid vertical={false} />

            {/* ✅ Axe des ordonnées ajouté */}
            <YAxis
              tickLine={false}
              axisLine={false}
              tickMargin={8}
              width={40}
              tickFormatter={(value) => `${value}%`}
            />

            {/* ✅ Axe des abscisses amélioré */}
            <XAxis
              dataKey="date"
              tickLine={false}
              axisLine={false}
              tickMargin={10}
              angle={-45}
              textAnchor="end"
              interval="preserveStartEnd"
              tickFormatter={(value) => {
                // Exemple de format: "Jan", "Fév", etc.
                const date = new Date(value);
                return date.toLocaleDateString("fr-FR", {
                  month: "short",
                  year: "2-digit",
                });
              }}
            />

            <ChartTooltip cursor={false} content={<ChartTooltipContent />} />

            <Line
              dataKey={portfolioGlobalName}
              type="monotone"
              stroke="#55A4FD"
              strokeWidth={2}
              dot={false}
            />
            <Line
              dataKey="S&P 500"
              type="monotone"
              stroke="#EF8CF8"
              strokeWidth={2}
              dot={false}
            />
          </LineChart>
        </ChartContainer>
      </CardContent>
    </Card>
  );
}
