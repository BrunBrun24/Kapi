import { z } from "zod";

export const formSchemaDatePortfolioBenchmark  = z.object({
  date: z.date(),
  portfolio: z.string(),
  benchmark: z.string(),
});
export type FormValuesDatePortfolioBenchmark = z.infer<
  typeof formSchemaDatePortfolioBenchmark 
>;

export const formSchemaYearPortfolioBenchmark = z.object({
  year: z.string(),
  portfolio: z.string(),
  benchmark: z.string(),
});
export type FormValuesYearPortfolioBenchmark = z.infer<
  typeof formSchemaYearPortfolioBenchmark
>;

// Chart pie
export const formSchemaType = z.object({
  type: z.string(),
});
export type FormValuesType = z.infer<
  typeof formSchemaType
>;
