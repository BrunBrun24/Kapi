"use client";

import { FormValuesYearPortfolioBenchmark } from "@/components/analytics/performance/type";
import { FormProvider, useFormContext } from "react-hook-form";

import { FormField } from "@/components/ui/form";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

export function FormYearPortfolioBenchmark() {
  const form = useFormContext<FormValuesYearPortfolioBenchmark>();

  const staticYears = [
    { label: "12 dernier mois", value: "12m" },
    { label: "2025", value: "2025" },
    { label: "2024", value: "2024" },
    { label: "2023", value: "2023" },
  ];

  return (
    <div className="flex flex-wrap items-center gap-4">
      {/* Select Portefeuille */}
      <FormProvider {...form}>
        {/* Select Benchmark */}
        <FormField
          control={form.control}
          name="benchmark"
          render={({ field }) => (
            <Select onValueChange={field.onChange} value={field.value}>
              <SelectTrigger className="w-[180px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectGroup>
                  <SelectLabel>Benchmarks</SelectLabel>
                  <SelectItem value="sp500">S&P 500</SelectItem>
                  <SelectItem value="nasdaq">Nasdaq 100</SelectItem>
                  <SelectItem value="cac40">CAC 40</SelectItem>
                </SelectGroup>
              </SelectContent>
            </Select>
          )}
        />

        <FormField
          control={form.control}
          name="year"
          render={({ field }) => (
            <Select
              onValueChange={field.onChange}
              value={field.value}
            >
              <SelectTrigger className="w-[160px]">
                <SelectValue placeholder="Choisir une année" />
              </SelectTrigger>
              <SelectContent>
                <SelectGroup>
                  <SelectLabel>Années</SelectLabel>
                  {staticYears.map((item) => (
                    <SelectItem key={item.value} value={item.value}>
                      {item.label}
                    </SelectItem>
                  ))}
                </SelectGroup>
              </SelectContent>
            </Select>
          )}
        />
      </FormProvider>
    </div>
  );
}
