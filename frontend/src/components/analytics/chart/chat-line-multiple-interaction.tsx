"use client";

import { CartesianGrid, Line, LineChart, XAxis, YAxis } from "recharts";

import { zodResolver } from "@hookform/resolvers/zod";
import { FormProvider, useForm } from "react-hook-form";

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
import {
  portfolioGlobalName,
  type PortfolioPerformances,
  type SelectedPortfolio,
  type UserPortfolio,
} from "@/components/analytics/type";
import { useEffect, useMemo, useState } from "react";
import api from "@/api";

const chartConfig = {
  desktop: {
    label: "Desktop",
    color: "#55A4FD",
  },
  mobile: {
    label: "Mobile",
    color: "#EF8CF8",
  },
} satisfies ChartConfig;


type ChartLineMultipleInteractionProps = {
  title: string;
  height: number;
  selectedPortfolio?: UserPortfolio;
};

export function ChartLineMultipleInteraction({
  title,
  height,
  selectedPortfolio,
}: ChartLineMultipleInteractionProps) {
  const form = useForm<FormValuesDatePortfolioBenchmark>({
    resolver: zodResolver(formSchemaDatePortfolioBenchmark),
    defaultValues: {
      date: undefined,
      portfolio: "all",
      benchmark: "S&P 500",
    },
  });
  type TwrEntry = { date: string; [key: string]: number | string };
  const [twr, setTwr] = useState<TwrEntry[]>([]);
  const [oldDate, setOldDate] = useState<Date>();

  type ValuationEntry = {
    date: string;
    [ticker: string]: number | string;
  };
  type TickersValuationData = [string, ValuationEntry[]][];
  const [tickersValuation, setTickersValuation] =
    useState<TickersValuationData>([]);

  const { watch } = form;

  const rawSelectedDate = watch("date");
  const selectedDate = useMemo(() => {
    if (!rawSelectedDate) return null;
    return new Date(rawSelectedDate).toISOString().slice(0, 10);
  }, [rawSelectedDate]);
  
  const selectedBenchmark = watch("benchmark");

  const tickersValuationDict = useMemo(() => {
    if (!tickersValuation || !selectedDate) return null;

    // 1. Trouver les données de la courbe "all"
    const allSeries = tickersValuation.find(
      ([label]) => label === portfolioGlobalName
    )?.[1];
    if (!allSeries) return null;

    // 2. Formater la date sélectionnée
    const targetDate = new Date(selectedDate).toISOString().slice(0, 10);

    // 3. Trouver la ligne correspondant à cette date
    const valuationAtDate = allSeries.find(
      (entry) => entry.date === targetDate
    );
    if (!valuationAtDate) return null;

    // 4. Créer le dictionnaire sans la clé "date"
    const { date, ...tickersDict } = valuationAtDate;
    return tickersDict;
  }, [tickersValuation, selectedDate]);

  useEffect(() => {
    if (!selectedDate || !tickersValuationDict || !selectedPortfolio) return;

    const fetchTwr = async () => {
      try {
        const res = await api.post(
          `/api/portfolio-performance/twr/${new Date(selectedDate)
            .toISOString()
            .slice(0, 10)}/${selectedPortfolio.id}/`,
          {
            tickers_valuations: tickersValuationDict,
          }
        );
        const data = res.data;
        setTwr(data.portfolio_twr);
      } catch (error) {
        console.error("Error fetching performance data:", error);
      }
    };

    fetchTwr();
  }, [selectedDate, tickersValuationDict, selectedPortfolio]);

  useEffect(() => {
    if (!selectedPortfolio?.id) return;

    const fetchData = async () => {
      try {
        const res = await api.get(
          `/api/portfolio-performance/${selectedPortfolio.id}/`,
          {
            params: {
              fields: "portfolio_twr, tickers_valuation",
            },
          }
        );
        const data = res.data;
        setTwr(data.portfolio_twr);
        setTickersValuation(data.tickers_valuation);

        if (!data.portfolio_twr || data.portfolio_twr.length === 0) return null;
          const firstEntry = data.portfolio_twr[0];
          setOldDate(new Date(firstEntry["date"]));
      } catch (error) {
        console.error("Error fetching performance data:", error);
      }
    };

    fetchData();
  }, [selectedPortfolio]);

  const latestTwrDate = useMemo(() => {
    if (!twr || twr.length === 0) return null;

    const firstEntry = twr[0];
    return new Date(firstEntry["date"]);
  }, [twr]);

  useEffect(() => {
    if (latestTwrDate) {
      form.setValue("date", latestTwrDate);
    }
  }, [latestTwrDate]);

  return (
    <Card>
      <CardHeader>
        <div className="flex flex-wrap items-center justify-between gap-4">
          <CardTitle className="text-2xl font-bold">{title}</CardTitle>
          {oldDate && (
            <FormProvider {...form}>
              <FormDatePortfolioBenchmark oldDate={oldDate} />
            </FormProvider>
          )}
        </div>
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
              bottom: 32,
            }} /* espace pour les ticks */
          >
            <CartesianGrid vertical={false} />

            {/* ✅ Axe Y avec suffixe % */}
            <YAxis
              tickLine={false}
              axisLine={false}
              tickMargin={8}
              width={50}
              tickFormatter={(value) => `${value}%`}
              /* ⬆️ si tes valeurs sont en décimal (0.125),
                 remplace par : value => `${(value * 100).toFixed(1)}%` */
            />

            {/* ✅ Axe X affichant uniquement l’année */}
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
              dataKey={selectedPortfolio?.name}
              type="monotone"
              stroke="var(--color-desktop)"
              strokeWidth={2}
              dot={false}
            />
            <Line
              dataKey={selectedBenchmark}
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
