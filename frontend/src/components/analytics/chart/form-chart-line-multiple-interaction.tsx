"use client";

import { useFormContext, FormProvider } from "react-hook-form";
import { format, subDays, subMonths, subYears } from "date-fns";
import { CalendarIcon } from "lucide-react";
import { FormValuesDatePortfolioBenchmark } from "@/components/analytics/performance/type";

import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Calendar } from "@/components/ui/calendar";
import {
  FormField,
  FormItem,
  FormControl,
  FormMessage,
} from "@/components/ui/form";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export function FormDatePortfolioBenchmark() {
  const form = useFormContext<FormValuesDatePortfolioBenchmark>();
  return (
    <div className="flex flex-wrap items-center gap-4">
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

        {/* Date Picker avec presets */}
        <FormField
          control={form.control}
          name="date"
          render={({ field }) => (
            <FormItem>
              <Popover>
                <PopoverTrigger asChild>
                  <FormControl>
                    <Button
                      variant="outline"
                      className={cn(
                        "w-[190px] justify-start text-left font-normal",
                        !field.value && "text-muted-foreground"
                      )}
                    >
                      <CalendarIcon className="mr-2 h-4 w-4" />
                      {field.value ? (
                        format(field.value, "PPP")
                      ) : (
                        <span>Choisir une date</span>
                      )}
                    </Button>
                  </FormControl>
                </PopoverTrigger>
                <PopoverContent className="w-auto p-4 space-y-2" align="start">
                  <Select
                    onValueChange={(value) => {
                      const today = new Date();
                      let newDate = today;

                      switch (value) {
                        case "1w":
                          newDate = subDays(today, 7);
                          break;
                        case "1m":
                          newDate = subMonths(today, 1);
                          break;
                        case "3m":
                          newDate = subMonths(today, 3);
                          break;
                        case "6m":
                          newDate = subMonths(today, 6);
                          break;
                        case "1y":
                          newDate = subYears(today, 1);
                          break;
                        case "5y":
                          newDate = subYears(today, 5);
                          break;
                        case "10y":
                          newDate = subYears(today, 10);
                          break;
                        case "all":
                          newDate = new Date("1900-01-01");
                          break;
                      }

                      field.onChange(newDate);
                    }}
                  >
                    <SelectTrigger className="w-full">
                      <SelectValue placeholder="Plage prédéfinie" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="1w">1 semaine</SelectItem>
                      <SelectItem value="1m">1 mois</SelectItem>
                      <SelectItem value="3m">3 mois</SelectItem>
                      <SelectItem value="6m">6 mois</SelectItem>
                      <SelectItem value="1y">1 an</SelectItem>
                      <SelectItem value="5y">5 ans</SelectItem>
                      <SelectItem value="10y">10 ans</SelectItem>
                      <SelectItem value="all">ALL</SelectItem>
                    </SelectContent>
                  </Select>

                  <Calendar
                    mode="single"
                    selected={field.value}
                    onSelect={field.onChange}
                    disabled={(date) => date > new Date()}
                    initialFocus
                  />
                </PopoverContent>
              </Popover>
              <FormMessage />
            </FormItem>
          )}
        />
      </FormProvider>
    </div>
  );
}
