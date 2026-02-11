"use client";

import api from "@/api";
import { ChartBarLabel } from "@/components/analytics/dividends/chart-bar-label";
import { ChartTooltipAdvanced } from "@/components/analytics/dividends/chart-tooltip-advanced";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { BarChart3, LineChart } from "lucide-react";
import { useEffect, useState } from "react";
import { UserPortfolio } from "../type";

type BarProps = {
  selectedPortfolio: UserPortfolio;
  height: number;
};

type TickerData = {
  month: string;
} & Record<string, number>; // tous les autres champs sont des tickers

export function Bar({ selectedPortfolio, height }: BarProps) {
  // Type de graphique (barres ou lignes)
  const [chartType, setChartType] = useState<"bar" | "tooltip">("bar");
  // Type de période (année ou mois)
  const [periodType, setPeriodType] = useState<"year" | "month">("year");
  // Année sélectionnée
  const [selectedYear, setSelectedYear] = useState<string>("");
  // Liste des années disponibles
  const [availableYears, setAvailableYears] = useState<number[]>([]);

  useEffect(() => {
    const fetchYears = async () => {
      try {
        const res = await api.get(
          `/api/portfolio/${selectedPortfolio.id}/performances/dividends/years-list/`
        );

        const years = res.data || [];
        setAvailableYears(years);

        // Sélection automatique de la dernière année
        if (years.length > 0) {
          setSelectedYear(years[years.length - 1].toString());
        }
      } catch (error) {
        console.error("Error fetching years:", error);
      }
    };

    fetchYears();
  }, [selectedPortfolio]);

  const [dividendsMonthData, setDividendsMonthData] = useState<
    Record<string, Record<string, number>>
  >({});
  useEffect(() => {
    const fetchDividends = async () => {
      try {
        const res = await api.get(
          `/api/portfolio/${selectedPortfolio.id}/performances/dividends/month/`
        );

        const data = res.data;
        setDividendsMonthData(data);
      } catch (error) {
        console.error("Error fetching years:", error);
      }
    };
    fetchDividends();
  }, [selectedPortfolio]);

  const [dividendsMonthTickerData, setDividendsMonthTickerData] = useState<
    { year: number; data: TickerData }[]
  >([]);

  useEffect(() => {
    const fetchDividends = async () => {
      try {
        const res = await api.get(
          `/api/portfolio/${selectedPortfolio.id}/performances/dividends/month/by-ticker/`
        );
        setDividendsMonthTickerData(res.data);
      } catch (error) {
        console.error("Error fetching dividends by ticker:", error);
      }
    };
    fetchDividends();
  }, [selectedPortfolio]);

  const [dividendsYearData, setDividendsYearData] = useState<
    Record<number, Record<string, number>>
  >({});
  useEffect(() => {
    const fetchDividends = async () => {
      try {
        const res = await api.get(
          `/api/portfolio/${selectedPortfolio.id}/performances/dividends/year/`
        );

        const data = res.data;
        setDividendsYearData(data);
      } catch (error) {
        console.error("Error fetching years:", error);
      }
    };
    fetchDividends();
  }, [selectedPortfolio]);

  const [dividendsYearTickerData, setDividendsYearTickerData] = useState<
    { data: TickerData }[]
  >([]);

  useEffect(() => {
    const fetchDividends = async () => {
      try {
        const res = await api.get(
          `/api/portfolio/${selectedPortfolio.id}/performances/dividends/year/by-ticker/`
        );
        setDividendsYearTickerData(res.data);
      } catch (error) {
        console.error("Error fetching dividends by ticker:", error);
      }
    };
    fetchDividends();
  }, [selectedPortfolio]);

  // On récupère uniquement les 'data' de l'année sélectionnée
  const filteredData: TickerData[] = selectedYear
    ? dividendsMonthTickerData
        .filter((d) => d.year === parseInt(selectedYear))
        .map((d) => d.data)
    : dividendsMonthTickerData.map((d) => d.data);

  return (
    <Card>
      <CardHeader>
        <div className="flex justify-between items-center w-full">
          <CardTitle>
            {/* Sélection entre Année et Mois */}
            <Select
              value={periodType}
              onValueChange={(value: "year" | "month") => setPeriodType(value)}
            >
              <SelectTrigger className="w-[100px]">
                <SelectValue placeholder="Période" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="year">Année</SelectItem>
                <SelectItem value="month">Mois</SelectItem>
              </SelectContent>
            </Select>
          </CardTitle>

          <div className="flex items-center gap-2">
            {/* Boutons de type de graphique */}
            <button
              title="Vue barres"
              onClick={() => setChartType("bar")}
              className={`w-8 h-8 border rounded flex items-center justify-center ${
                chartType === "bar" ? "bg-muted" : "hover:bg-muted"
              }`}
            >
              <BarChart3 className="w-4 h-4" />
            </button>

            <button
              title="Vue lignes"
              onClick={() => setChartType("tooltip")}
              className={`w-8 h-8 border rounded flex items-center justify-center ${
                chartType === "tooltip" ? "bg-muted" : "hover:bg-muted"
              }`}
            >
              <LineChart className="w-4 h-4" />
            </button>

            {/* Sélecteur d’année */}
            {periodType === "month" && (
              <Select
                value={selectedYear}
                onValueChange={(value) => setSelectedYear(value)}
              >
                <SelectTrigger className="w-[100px]">
                  <SelectValue placeholder="Année" />
                </SelectTrigger>
                <SelectContent>
                  {availableYears.map((year) => (
                    <SelectItem key={year} value={year.toString()}>
                      {year}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          </div>
        </div>
      </CardHeader>

      <CardContent className="flex justify-center">
        {chartType === "bar" ? (
          periodType === "month" ? (
            <ChartBarLabel
              chartData={dividendsMonthData[selectedYear] || {}}
              height={height}
            />
          ) : (
            <ChartBarLabel
              chartData={Object.fromEntries(
                Object.entries(dividendsYearData).map(([year, tickers]) => [
                  year,
                  // Si tickers est déjà un nombre (comme dans ton exemple {2023: 0.87}), on retourne juste tickers
                  typeof tickers === "number"
                    ? tickers
                    : Object.values(tickers).reduce((sum, val) => sum + val, 0),
                ])
              )}
              height={height}
            />
          )
        ) : periodType === "month" ? (
          <ChartTooltipAdvanced chartData={filteredData} height={height} />
        ) : (
          <ChartTooltipAdvanced
            chartData={dividendsYearTickerData}
            height={height}
          />
        )}
      </CardContent>
    </Card>
  );
}
