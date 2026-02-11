'use client';

import { useEffect, useState } from 'react';
import {
  getAvailableYears,
  getMonthData,
  getMonthDataByTicker,
  getYearData,
  getYearDataByTicker,
} from '@/components/analytics/hooks/generic-bar';

import { ChartBarLabel } from '@/components/analytics/dividends/chart-bar-label';
import { ChartTooltipAdvanced } from '@/components/analytics/dividends/chart-tooltip-advanced';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { BarChart3, LineChart } from 'lucide-react';
import { UserPortfolio } from '../type';

type Props = {
  selectedPortfolio: UserPortfolio;
  height: number;
  title: string;
  dataType: 'dividends' | 'investissements';
};

type TickerData = {
  month: string;
} & Record<string, number>;

export function GenericBarChart({ selectedPortfolio, height, title, dataType }: Props) {
  const [chartType, setChartType] = useState<'bar' | 'tooltip'>('bar');
  const [periodType, setPeriodType] = useState<'year' | 'month'>('year');
  const [selectedYear, setSelectedYear] = useState<string>('');
  const [availableYears, setAvailableYears] = useState<number[]>([]);

  const [monthData, setMonthData] = useState<Record<string, Record<string, number>>>({});
  const [monthTickerData, setMonthTickerData] = useState<
    { year: number; data: TickerData }[]
  >([]);
  const [yearData, setYearData] = useState<Record<number, Record<string, number>>>({});
  const [yearTickerData, setYearTickerData] = useState<{ data: TickerData }[]>([]);

  // 🔹 Fetch toutes les données selon le type
  useEffect(() => {
    if (!selectedPortfolio?.id) return;

    (async () => {
      try {
        const years = await getAvailableYears(selectedPortfolio.id, dataType);
        setAvailableYears(years);
        if (years.length > 0) setSelectedYear(years[years.length - 1].toString());

        const [month, monthTicker, year, yearTicker] = await Promise.all([
          getMonthData(selectedPortfolio.id, dataType),
          getMonthDataByTicker(selectedPortfolio.id, dataType),
          getYearData(selectedPortfolio.id, dataType),
          getYearDataByTicker(selectedPortfolio.id, dataType),
        ]);

        setMonthData(month);
        setMonthTickerData(monthTicker);
        setYearData(year);
        setYearTickerData(yearTicker);
      } catch (error) {
        console.error(`Error fetching ${dataType} data:`, error);
      }
    })();
  }, [selectedPortfolio, dataType]);

  const filteredData: TickerData[] = selectedYear
    ? monthTickerData.filter((d) => d.year === parseInt(selectedYear)).map((d) => d.data)
    : monthTickerData.map((d) => d.data);

  return (
    <Card>
      <CardHeader>
        <div className="flex justify-between items-center w-full">
          {/* Titre + Sélecteur de période alignés à gauche */}
          <div className="flex items-center gap-4">
            <CardTitle className="text-2xl font-bold">{title}</CardTitle>
            <Select
              value={periodType}
              onValueChange={(value: 'year' | 'month') => setPeriodType(value)}
            >
              <SelectTrigger className="w-[120px]">
                <SelectValue placeholder="Période" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="year">Année</SelectItem>
                <SelectItem value="month">Mois</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Boutons et sélecteur d'année alignés à droite */}
          <div className="flex items-center gap-2">
            <button
              title="Vue barres"
              onClick={() => setChartType('bar')}
              className={`w-8 h-8 border rounded flex items-center justify-center ${
                chartType === 'bar' ? 'bg-muted' : 'hover:bg-muted'
              }`}
            >
              <BarChart3 className="w-4 h-4" />
            </button>

            <button
              title="Vue lignes"
              onClick={() => setChartType('tooltip')}
              className={`w-8 h-8 border rounded flex items-center justify-center ${
                chartType === 'tooltip' ? 'bg-muted' : 'hover:bg-muted'
              }`}
            >
              <LineChart className="w-4 h-4" />
            </button>

            {periodType === 'month' && (
              <Select value={selectedYear} onValueChange={setSelectedYear}>
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
        {chartType === 'bar' ? (
          periodType === 'month' ? (
            <ChartBarLabel chartData={monthData[selectedYear] || {}} height={height} />
          ) : (
            <ChartBarLabel
              chartData={Object.fromEntries(
                Object.entries(yearData).map(([year, tickers]) => [
                  year,
                  typeof tickers === 'number'
                    ? tickers
                    : Object.values(tickers).reduce((sum, val) => sum + val, 0),
                ])
              )}
              height={height}
            />
          )
        ) : periodType === 'month' ? (
          <ChartTooltipAdvanced chartData={filteredData} height={height} />
        ) : (
          <ChartTooltipAdvanced chartData={yearTickerData} height={height} />
        )}
      </CardContent>
    </Card>
  );
}
