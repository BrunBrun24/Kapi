"use client";

import { ChartBarLabel } from "@/components/analytics/dividends/chart-bar-label";
import { ChartTooltipAdvanced } from "@/components/analytics/dividends/chart-tooltip-advanced";
import { BarChart3, LineChart } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useState } from "react";

type ChartBarLabelProps = {
  title: string;
  height: number;
  selectedYear?: boolean;
};

export function BarMonth({
  title,
  height,
  selectedYear = false,
}: ChartBarLabelProps) {
  const [chartType, setChartType] = useState<"bar" | "tooltip">("bar");

  return (
    <Card>
      <CardHeader>
        <div className="flex justify-between items-center w-full">
          <CardTitle>{title}</CardTitle>

          <div className="flex items-center gap-2">
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

            {selectedYear && (
              <Select defaultValue="2025">
                <SelectTrigger className="w-[100px]">
                  <SelectValue placeholder="Année" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="2022">2022</SelectItem>
                  <SelectItem value="2023">2023</SelectItem>
                  <SelectItem value="2024">2024</SelectItem>
                  <SelectItem value="2025">2025</SelectItem>
                </SelectContent>
              </Select>
            )}
          </div>
        </div>
      </CardHeader>

      <CardContent className="flex justify-center">
        {chartType === "bar" ? (
          <ChartBarLabel height={height} />
        ) : (
          <ChartTooltipAdvanced height={height} />
        )}
      </CardContent>
    </Card>
  );
}
