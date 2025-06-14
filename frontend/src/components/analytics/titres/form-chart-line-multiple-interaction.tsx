"use client";

import { FormValuesType } from "@/components/analytics/performance/type";
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

export function FormType() {
  const form = useFormContext<FormValuesType>();
  return (
    <div className="flex flex-wrap items-center gap-4">
      {/* Select Portefeuille */}
      <FormProvider {...form}>
        <FormField
          control={form.control}
          name="type"
          render={({ field }) => (
            <Select onValueChange={field.onChange} value={field.value}>
              <SelectTrigger className="w-[180px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectGroup>
                  <SelectLabel>Type</SelectLabel>
                  <SelectItem value="all">All</SelectItem>
                  <SelectItem value="action">Actions</SelectItem>
                  <SelectItem value="etf">ETF</SelectItem>
                </SelectGroup>
              </SelectContent>
            </Select>
          )}
        />
      </FormProvider>
    </div>
  );
}
