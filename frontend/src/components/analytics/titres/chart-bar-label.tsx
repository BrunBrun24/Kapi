"use client";

import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";
import {
    ChartContainer,
    ChartTooltip,
    ChartTooltipContent,
} from "@/components/ui/chart";
import {
    Menubar
} from "@/components/ui/menubar";
import React, { useState } from "react";
import {
    Bar,
    BarChart,
    CartesianGrid,
    Cell,
    LabelList,
    XAxis,
    YAxis,
} from "recharts";

type CustomTickProps = {
  x: number;
  y: number;
  payload: {
    value: string;
  };
  data: {
    ticker: string;
    companyName: string;
    logoUrl: string;
  }[];
};

export const CustomTick: React.FC<CustomTickProps> = ({
  x,
  y,
  payload,
  data,
}) => {
  const item = data.find((d) => d.ticker === payload.value);
  if (!item) return null;

  const logoSize = 30;
  const logoYOffset = -8;
  const tickerYOffset = 12;
  const nameYOffset = 33;

  return (
    <g transform={`translate(${x}, ${y + 10})`}>
      {/* Logo à gauche */}
      <image
        href={item.logoUrl}
        x={-logoSize / 2 - 10}
        y={logoYOffset}
        width={logoSize}
        height={logoSize}
        preserveAspectRatio="xMidYMid slice"
      />

      {/* Ticker à droite du logo */}
      <text
        x={logoSize / 2.5}
        y={tickerYOffset}
        fontSize={11}
        fontWeight="bold"
        fill="black"
        textAnchor="start"
      >
        {item.ticker}
      </text>

      {/* Nom de la compagnie en dessous */}
      <text x={10} y={nameYOffset} fontSize={9} fill="#555" textAnchor="middle">
        {item.companyName}
      </text>
    </g>
  );
};

type ChartBarLabelProps = {
  height?: number;
};

const datasets: Record<string, any[]> = {
  Montant: [
    {
      companyName: "Apple",
      ticker: "AAPL",
      logoUrl: "https://logo.clearbit.com/apple.com",
      value: 186,
    },
    {
      companyName: "Meta",
      ticker: "META",
      logoUrl: "https://logo.clearbit.com/meta.com",
      value: 214,
    },
    {
      companyName: "Microsoft",
      ticker: "MSFT",
      logoUrl: "https://logo.clearbit.com/microsoft.com",
      value: 305,
    },
    {
      companyName: "Tesla",
      ticker: "TSLA",
      logoUrl: "https://logo.clearbit.com/tesla.com",
      value: -73,
    },
  ],
  "%": [
    {
      companyName: "Microsoft",
      ticker: "MSFT",
      logoUrl: "https://logo.clearbit.com/microsoft.com",
      value: 305,
    },
    {
      companyName: "Tesla",
      ticker: "TSLA",
      logoUrl: "https://logo.clearbit.com/tesla.com",
      value: -73,
    },
    {
      companyName: "Google",
      ticker: "GOOGL",
      logoUrl: "https://logo.clearbit.com/google.com",
      value: 209,
    },
    {
      companyName: "Amazon",
      ticker: "AMZN",
      logoUrl: "https://logo.clearbit.com/amazon.com",
      value: 237,
    },
  ],
  "% / an": [
    {
      companyName: "Google",
      ticker: "GOOGL",
      logoUrl: "https://logo.clearbit.com/google.com",
      value: 209,
    },
    {
      companyName: "Amazon",
      ticker: "AMZN",
      logoUrl: "https://logo.clearbit.com/amazon.com",
      value: 237,
    },
    {
      companyName: "Microsoft",
      ticker: "MSFT",
      logoUrl: "https://logo.clearbit.com/microsoft.com",
      value: 305,
    },
    {
      companyName: "Tesla",
      ticker: "TSLA",
      logoUrl: "https://logo.clearbit.com/tesla.com",
      value: -73,
    },
  ],
  "S&pP500": [
    {
      companyName: "Google",
      ticker: "GOOGL",
      logoUrl: "https://logo.clearbit.com/google.com",
      value: 209,
    },
    {
      companyName: "Amazon",
      ticker: "AMZN",
      logoUrl: "https://logo.clearbit.com/amazon.com",
      value: 237,
    },
    {
      companyName: "Microsoft",
      ticker: "MSFT",
      logoUrl: "https://logo.clearbit.com/microsoft.com",
      value: 305,
    },
    {
      companyName: "Tesla",
      ticker: "TSLA",
      logoUrl: "https://logo.clearbit.com/tesla.com",
      value: -73,
    },
  ],
};

export function ChartBarLabel({ height = 500 }: ChartBarLabelProps) {
  const [selectedSet, setSelectedSet] =
    useState<keyof typeof datasets>("Montant");

  const chartData = datasets[selectedSet];

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader className="pb-2">
          <div className="flex justify-between items-start">
            <div>
              <CardTitle className="text-2xl font-bold">Performance</CardTitle>
              <CardDescription>
                Le montant et pourcentage de gains / pertes sur vos positions
                actuelles
              </CardDescription>
            </div>
            <Menubar className="gap-4">
              {Object.keys(datasets).map((key) => (
                <div
                  key={key}
                  onClick={() => setSelectedSet(key)}
                  className={`cursor-pointer px-4 py-1 rounded-md font-medium ${
                    selectedSet === key
                      ? "bg-blue-100 text-blue-600"
                      : "hover:bg-muted"
                  }`}
                >
                  {key}
                </div>
              ))}
            </Menubar>
          </div>
        </CardHeader>
        <CardContent>
          <ChartContainer
            config={{}}
            style={{ height }}
            className="mx-auto w-full"
          >
            <BarChart data={chartData} margin={{ top: 20, bottom: 40 }}>
              <CartesianGrid vertical={false} strokeDasharray="3 3" />
              <YAxis
                tickLine={false}
                axisLine={false}
                tick={{ fontSize: 12 }}
              />
              <XAxis
                dataKey="ticker"
                tickLine={false}
                axisLine={false}
                tickMargin={20}
                tick={(props) => <CustomTick {...props} data={chartData} />}
              />
              <ChartTooltip
                cursor={false}
                content={<ChartTooltipContent hideLabel />}
              />
              <Bar dataKey="value" radius={8}>
                {chartData.map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={entry.value >= 0 ? "#22c55e" : "#ef4444"}
                  />
                ))}
                <LabelList
                  dataKey="value"
                  position="top"
                  offset={12}
                  className="fill-foreground"
                  fontSize={12}
                />
              </Bar>
            </BarChart>
          </ChartContainer>
        </CardContent>
      </Card>
    </div>
  );
}
