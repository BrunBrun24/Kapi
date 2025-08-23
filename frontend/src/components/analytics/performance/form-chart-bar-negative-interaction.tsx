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

type FormYearPortfolioBenchmarkProps = {
  yearOptions: { label: string; value: string }[];
};

export function FormYearPortfolioBenchmark({
  yearOptions,
}: FormYearPortfolioBenchmarkProps) {
  const form = useFormContext<FormValuesYearPortfolioBenchmark>();

  return (
    <div className="flex flex-wrap items-center gap-4">
      {/* Benchmark select inchangé */}
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
                <SelectItem value="S&P 500">S&P 500</SelectItem>
                <SelectItem value="Nasdaq 100">Nasdaq 100</SelectItem>
                <SelectItem value="MSCI WORLD">MSCI WORLD</SelectItem>
                <SelectItem value="CAC 40">CAC 40</SelectItem>
              </SelectGroup>
            </SelectContent>
          </Select>
        )}
      />

      <FormField
        control={form.control}
        name="year"
        render={({ field }) => (
          <Select onValueChange={field.onChange} value={field.value}>
            <SelectTrigger className="w-[160px]">
              <SelectValue placeholder="Choisir une année" />
            </SelectTrigger>
            <SelectContent>
              <SelectGroup>
                <SelectLabel>Années</SelectLabel>
                {yearOptions.map((item) => (
                  <SelectItem key={item.value} value={item.value}>
                    {item.label}
                  </SelectItem>
                ))}
              </SelectGroup>
            </SelectContent>
          </Select>
        )}
      />
    </div>
  );
}
