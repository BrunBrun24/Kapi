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
import { useEffect, useState } from "react";
import api from "@/api";
import { UserPortfolio } from "../type";

type MonthlyPercentage = Record<
  string, // benchmark ex: 'S&P 500 DCA'
  Record<
    string, // year ex: '2024'
    Record<string, number> // month ex: 'Jan': -4.5
  >
>;

const monthsOrder = [
  "Jan",
  "Feb",
  "Mar",
  "Apr",
  "May",
  "Jun",
  "Jul",
  "Aug",
  "Sep",
  "Oct",
  "Nov",
  "Dec",
];

// Fonction utilitaire pour récupérer 12 derniers mois à partir d'une date donnée
function getLast12Months(fromDate: Date): { year: string; month: string }[] {
  const result = [];
  let year = fromDate.getFullYear();
  let monthIndex = fromDate.getMonth(); // 0-based: Jan=0, Jul=6 etc

  for (let i = 0; i < 12; i++) {
    // Convertir monthIndex en nom de mois (ex: 0 -> "Jan")
    const month = monthsOrder[monthIndex];

    result.unshift({ year: year.toString(), month });

    // Décrémenter le mois (aller vers mois précédent)
    monthIndex--;
    if (monthIndex < 0) {
      monthIndex = 11; // Décembre
      year--;
    }
  }

  return result;
}

function buildChartData(
  data: MonthlyPercentage,
  selectedBenchmark: string,
  selectedYear: string
): { month: string; percentage: number | null }[] {
  if (!data || !selectedBenchmark || !selectedYear) return [];

  const benchmarkData = data[selectedBenchmark];
  if (!benchmarkData) return [];

  if (selectedYear === "12m") {
    // On récupère la date actuelle
    const now = new Date();

    // 12 derniers mois, ex: [{year:"2024",month:"Aug"},...,{year:"2025",month:"Jul"}]
    const last12Months = getLast12Months(now);

    return last12Months.map(({ year, month }) => {
      const yearData = benchmarkData[year];
      const value = yearData ? yearData[month] : null;
      return {
        month,
        percentage: value != null ? Number(value.toFixed(2)) : null,
      };
    });
  } else {
    // Cas normal année unique
    const yearData = benchmarkData[selectedYear];
    if (!yearData) return [];

    // On filtre les mois présents
    const availableMonths = monthsOrder.filter(
      (month) => yearData[month] != null
    );

    return availableMonths.map((month) => {
      const value = yearData[month];
      return {
        month,
        percentage: value != null ? Number(value.toFixed(2)) : null,
      };
    });
  }
}

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
  value?: string | number | null;
}) {
  if (value == null || x == null || y == null || width == null) return null;

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

function extractAvailableYears(
  data: Record<string, Record<string, unknown>>
): string[] {
  const yearSet = new Set<string>();

  for (const benchmarkName in data) {
    const benchmarkData = data[benchmarkName];
    for (const year of Object.keys(benchmarkData)) {
      yearSet.add(year);
    }
  }

  return Array.from(yearSet).sort((a, b) => Number(b) - Number(a));
}

function buildYearOptions(data: Record<string, Record<string, unknown>>) {
  const dynamicYears = extractAvailableYears(data);

  const yearOptions = [
    { label: "12 derniers mois", value: "12m" },
    ...dynamicYears.map((year) => ({
      label: year,
      value: year,
    })),
  ];

  return yearOptions;
}

function mergeChartData(
  portfolioData: { month: string; percentage: number | null }[],
  benchmarkData: { month: string; percentage: number | null }[]
) {
  const merged = portfolioData.map((item) => {
    const matchingBenchmark = benchmarkData.find((b) => b.month === item.month);
    return {
      month: item.month,
      portfolio: item.percentage,
      benchmark: matchingBenchmark?.percentage ?? null,
    };
  });

  return merged;
}

type ChartBarNegativeInteractionProps = {
  title: string;
  height: number;
  selectedPortfolio?: UserPortfolio;
};

export function ChartBarNegativeInteraction({
  title,
  height,
  selectedPortfolio,
}: ChartBarNegativeInteractionProps) {
  const form = useForm<FormValuesYearPortfolioBenchmark>({
    resolver: zodResolver(formSchemaYearPortfolioBenchmark),
    defaultValues: {
      year: "12m",
      portfolio: "all",
      benchmark: "S&P 500",
    },
  });

  const [monthlyPercentage, setMonthlyPercentage] = useState<MonthlyPercentage>(
    {}
  );
  const [yearOptions, setYearOptions] = useState<
    { label: string; value: string }[]
  >([]);

  const selectedYear = form.watch("year");
  const selectedBenchmark = form.watch("benchmark");

  const chartDataPorfolio = buildChartData(
    monthlyPercentage,
    selectedPortfolio?.name,
    selectedYear
  );

  const chartDataBenchmark = buildChartData(
    monthlyPercentage,
    selectedBenchmark,
    selectedYear
  );

  const mergedChartData = mergeChartData(chartDataPorfolio, chartDataBenchmark);

  useEffect(() => {
    if (!selectedPortfolio?.id) return;

    const fetchData = async () => {
      try {
        const res = await api.get(
          `/api/portfolio-performance/${selectedPortfolio.id}/`,
          { params: { fields: "portfolio_monthly_percentages" } }
        );

        const data = res.data.portfolio_monthly_percentages;
        setMonthlyPercentage(data);

        const years = buildYearOptions(data);
        setYearOptions(years);
      } catch (error) {
        console.error("Erreur lors du chargement des performances :", error);
      }
    };

    fetchData();
  }, [selectedPortfolio]);

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between flex-wrap gap-4">
          <CardTitle className="text-2xl font-bold">{title}</CardTitle>
          <FormProvider {...form}>
            <FormYearPortfolioBenchmark yearOptions={yearOptions} />
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
            data={mergedChartData}
            margin={{ top: 20, right: 30, left: 20, bottom: 20 }}
          >
            <CartesianGrid vertical={false} strokeDasharray="3 3" />
            <XAxis dataKey="month" />
            <YAxis
              domain={["dataMin - 5", "dataMax + 5"]}
              padding={{ top: 10, bottom: 10 }}
              tickFormatter={(value) => value.toFixed(2)}
            />

            <ReferenceLine y={0} stroke="#ccc" strokeWidth={1} />
            <ChartTooltip
              cursor={{ fill: "transparent" }}
              content={<ChartTooltipContent hideLabel hideIndicator />}
            />

            {/* Portfolio */}
            <Bar dataKey="portfolio" name="Portefeuille" fill="#55A4FD">
              <LabelList dataKey="portfolio" content={renderCustomLabel} />
            </Bar>

            {/* Benchmark */}
            <Bar dataKey="benchmark" name="Benchmark" fill="#EF8CF8">
              <LabelList dataKey="benchmark" content={renderCustomLabel} />
            </Bar>
          </BarChart>
        </ChartContainer>
      </CardContent>
    </Card>
  );
}
