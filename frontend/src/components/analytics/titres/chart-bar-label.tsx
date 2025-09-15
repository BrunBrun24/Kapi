import api from "@/api";
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
import { Menubar } from "@/components/ui/menubar";
import React, { useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  LabelList,
  XAxis,
  YAxis,
} from "recharts";
import { UserPortfolio } from "../type";

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
  const maxNameLength = 12; // nombre maximum de caractères à afficher

  // Tronquer le nom si trop long
  const displayName =
    item.companyName.length > maxNameLength
      ? item.companyName.slice(0, maxNameLength) + "…"
      : item.companyName;

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

      {/* Nom de la compagnie tronqué */}
      <text x={10} y={nameYOffset} fontSize={9} fill="#555" textAnchor="middle">
        {displayName}
      </text>
    </g>
  );
};

type ChartBarLabelProps = {
  selectedPortfolio?: UserPortfolio;
  height?: number;
};

export function ChartBarLabel({
  selectedPortfolio,
  height = 500,
}: ChartBarLabelProps) {
  const [performances, setPerformances] = useState<Record<string, any[]>>({});
  const [selectedSet, setSelectedSet] = useState<string>("%");
  const [chartData, setChartData] = useState<any[]>([]);

  useEffect(() => {
    if (!selectedPortfolio?.id) return;

    const fetchData = async () => {
      try {
        const res = await api.get(
          `/api/portfolio/${selectedPortfolio.id}/performances/`
        );
        setPerformances(res.data);
        setChartData(res.data[selectedSet]);
      } catch (error) {
        console.error("Error fetching performance data:", error);
      }
    };

    fetchData();
  }, [selectedPortfolio]);

  useEffect(() => {
    if (performances && selectedSet in performances) {
      setChartData(performances[selectedSet]);
    }
  }, [selectedSet, performances]);

  // Fonction utilitaire pour formatter le label selon le type de dataset
  const formatValue = (value: number) => {
    if (selectedSet === "Montant") return `${value} €`;
    if (selectedSet === "%" || selectedSet === "% / an") return `${value} %`;
    if (selectedSet.toLowerCase().includes("sp500")) return `${value} pts`;
    return value;
  };

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
              {Object.keys(performances).map((key) => (
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
                formatter={(value: any) => formatValue(value)}
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
                  formatter={(value: number | string) =>
                    formatValue(Number(value))
                  }
                />
              </Bar>
            </BarChart>
          </ChartContainer>
        </CardContent>
      </Card>
    </div>
  );
}
