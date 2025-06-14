"use client";

import { IconX } from "@tabler/icons-react";
import {
  ColumnDef,
  ColumnFiltersState,
  flexRender,
  getCoreRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  SortingState,
  useReactTable,
  VisibilityState,
} from "@tanstack/react-table";
import {
  ArrowUpDown,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  ChevronsLeft,
  ChevronsRight,
  MoreHorizontal,
} from "lucide-react";
import * as React from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Command,
  CommandGroup,
  CommandInput,
  CommandItem,
} from "@/components/ui/command";
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Input } from "@/components/ui/input";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

import { TableDataTransaction } from "@/components/analytics/titres/board/type";
import {
  Pagination,
  PaginationContent,
  PaginationItem,
} from "@/components/ui/pagination";

const data: TableDataTransaction[] = [
  {
    id: 1,
    ticker: "AAPL",
    name: "Apple Inc.",
    logo: "https://logo.clearbit.com/apple.com",
    date: new Date("2023-01-10"),
    type: "buy",
    quantity: 10,
    amountInvest: 1500,
    stockValue: 150,
    fees: 5,
  },
  {
    id: 2,
    ticker: "AAPL",
    name: "Apple Inc.",
    logo: "https://logo.clearbit.com/apple.com",
    date: new Date("2024-03-12"),
    type: "sell",
    quantity: 5,
    amountInvest: 900,
    stockValue: 180,
    fees: 3,
  },
  {
    id: 3,
    ticker: "MSFT",
    name: "Microsoft Corp.",
    logo: "https://logo.clearbit.com/microsoft.com",
    date: new Date("2022-12-01"),
    type: "buy",
    quantity: 8,
    amountInvest: 2000,
    stockValue: 250,
    fees: 4,
  },
];

type NumberCondition = "positive" | "negative" | "gt100" | "gt500" | "gt1000";

const CONDITIONS: { label: string; value: NumberCondition }[] = [
  { label: "Positif", value: "positive" },
  { label: "> 100", value: "gt100" },
  { label: "> 500", value: "gt500" },
  { label: "> 1000", value: "gt1000" },
];

type FilterOption<T> = {
  label: string;
  value: T;
};

interface GenericFilterComboboxProps<T> {
  label: string;
  options: FilterOption<T>[];
  selectedValues: T[];
  onChange: (values: T[]) => void;
  counts?: Record<string, number>;
  capitalize?: boolean;
}

export function GenericFilterCombobox<T extends string | number>({
  label,
  options,
  selectedValues,
  onChange,
  counts,
  capitalize = false,
}: GenericFilterComboboxProps<T>) {
  const [open, setOpen] = React.useState(false);

  const toggleValue = (value: T) => {
    const newValues = selectedValues.includes(value)
      ? selectedValues.filter((v) => v !== value)
      : [...selectedValues, value];
    onChange(newValues);
  };

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          className="ml-2 min-w-[100px] w-auto justify-between"
        >
          {label}
          <ChevronDown className="ml-2 h-4 w-4" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-[200px] p-0">
        <Command>
          <CommandInput placeholder={`Filtrer ${label}...`} />
          <CommandGroup>
            {options.map((option) => (
              <CommandItem
                key={String(option.value)}
                onSelect={() => toggleValue(option.value)}
                className="flex justify-between"
              >
                <div className="flex items-center space-x-2">
                  <Checkbox
                    checked={selectedValues.includes(option.value)}
                    onCheckedChange={() => toggleValue(option.value)}
                  />
                  <span className={capitalize ? "capitalize" : ""}>
                    {option.label}
                  </span>
                </div>
                {counts && (
                  <span className="text-muted-foreground">
                    {counts[option.value as string]}
                  </span>
                )}
              </CommandItem>
            ))}
          </CommandGroup>
        </Command>
      </PopoverContent>
    </Popover>
  );
}

const numberFilterFn = (
  row: any,
  columnId: string,
  filterValue: NumberCondition[]
) => {
  const rawValue = row.getValue(columnId);

  const value = typeof rawValue === "number" ? rawValue : Number(rawValue);
  if (isNaN(value)) return false;

  return filterValue.every((condition) => {
    switch (condition) {
      case "positive":
        return value > 0;
      case "gt100":
        return value > 100;
      case "gt500":
        return value > 500;
      case "gt1000":
        return value > 1000;
      default:
        return true;
    }
  });
};

const stringOrFilterFn = (
  row: any,
  columnId: string,
  filterValue: string[]
) => {
  if (!filterValue?.length) return true;
  const value = row.getValue(columnId);
  return filterValue.includes(value);
};

const columns: ColumnDef<TableDataTransaction>[] = [
  {
    accessorKey: "ticker",
    header: "Ticker",
    cell: ({ row }) => {
      const logoUrl = row.original.logo;
      const companyName = row.original.name;
      const ticker = row.original.ticker;

      return (
        <div className="flex items-center gap-2">
          <img
            src={logoUrl}
            alt={ticker}
            className="w-8 h-8"
          />
          <div className="flex flex-col leading-tight">
            <span className="font-medium text-sm">{companyName}</span>
            <span className="text-muted-foreground text-xs">{ticker}</span>
          </div>
        </div>
      );
    },
    filterFn: stringOrFilterFn,
  },
  {
    accessorKey: "date",
    header: ({ column }) => (
      <Button
        variant="ghost"
        onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
      >
        Date
        <ArrowUpDown className="ml-2 h-4 w-4" />
      </Button>
    ),
    cell: ({ getValue }) =>
      new Date(getValue() as string).toLocaleDateString("fr-FR"),
  },
  {
    accessorKey: "type",
    header: "Type",
    cell: ({ getValue }) => (getValue() === "buy" ? "Achat" : "Vente"),
    filterFn: stringOrFilterFn,
  },
  {
    accessorKey: "quantity",
    header: ({ column }) => (
      <Button
        variant="ghost"
        onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
      >
        Quantité
        <ArrowUpDown className="ml-2 h-4 w-4" />
      </Button>
    ),
  },
  {
    accessorKey: "amountInvest",
    header: ({ column }) => (
      <Button
        variant="ghost"
        onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
      >
        Montant investi
        <ArrowUpDown className="ml-2 h-4 w-4" />
      </Button>
    ),
    cell: ({ getValue }) => `${getValue()} €`,
    filterFn: numberFilterFn,
  },
  {
    accessorKey: "stockValue",
    header: "Valeur du ticker",
    cell: ({ getValue }) => `${getValue()} €`,
  },
  {
    accessorKey: "fees",
    header: ({ column }) => (
      <Button
        variant="ghost"
        onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
      >
        Frais
        <ArrowUpDown className="ml-2 h-4 w-4" />
      </Button>
    ),
    cell: ({ getValue }) => `${getValue()} €`,
  },
];

function getFilterMeta<T>(
  table: ReturnType<typeof useReactTable<T>>,
  columnKey: keyof T,
  data: T[]
) {
  const options = Array.from(
    new Set(data.map((item) => String(item[columnKey])))
  );

  const selectedValues =
    (table.getColumn(columnKey as string)?.getFilterValue() as string[]) ?? [];

  const counts = options.reduce((acc, value) => {
    acc[value] = data.filter((d) => String(d[columnKey]) === value).length;
    return acc;
  }, {} as Record<string, number>);

  return { options, selectedValues, counts };
}

function formatOptions(values: string[]) {
  return values.map((val) => ({
    label: val,
    value: val,
  }));
}

export function BoardTransactions() {
  const [sorting, setSorting] = React.useState<SortingState>([]);
  const [columnFilters, setColumnFilters] = React.useState<ColumnFiltersState>(
    []
  );
  const [columnVisibility, setColumnVisibility] =
    React.useState<VisibilityState>({});
  const [rowSelection, setRowSelection] = React.useState({});

  const table = useReactTable({
    data,
    columns,
    state: {
      sorting,
      columnFilters,
      columnVisibility,
      rowSelection,
    },
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    onColumnVisibilityChange: setColumnVisibility,
    onRowSelectionChange: setRowSelection,
    getCoreRowModel: getCoreRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
  });

  const tickerMeta = getFilterMeta(table, "ticker", data);
  const formattedTickerOptions = formatOptions(tickerMeta.options);

  const typeMeta = getFilterMeta(table, "type", data);
  const formattedTypeOptions = formatOptions(typeMeta.options);

  const [selectedAmountConditions, setSelectedAmountConditions] =
    React.useState<NumberCondition[]>([]);

  const hasActiveFilters = () =>
    columnFilters.some((filter) => {
      const value = filter.value;
      if (Array.isArray(value)) return value.length > 0;
      return value !== undefined && value !== null && value !== "";
    });

  return (
    <div className="w-full">
      <Card className="flex flex-col">
        <CardContent>
          <div className="flex items-center py-4 space-x-2 w-full">
            <GenericFilterCombobox<string>
              label="Type"
              options={formattedTypeOptions}
              selectedValues={typeMeta.selectedValues}
              onChange={(newValues) => {
                table.getColumn("type")?.setFilterValue(newValues);
              }}
              counts={typeMeta.counts}
              capitalize
            />

            <GenericFilterCombobox<string>
              label="Ticker"
              options={formattedTickerOptions}
              selectedValues={tickerMeta.selectedValues}
              onChange={(newValues) => {
                table.getColumn("ticker")?.setFilterValue(newValues);
              }}
              counts={tickerMeta.counts}
              capitalize
            />

            <GenericFilterCombobox<NumberCondition>
              label="Montant investi"
              options={CONDITIONS}
              selectedValues={selectedAmountConditions}
              onChange={(newConditions) => {
                setSelectedAmountConditions(newConditions);
                table.getColumn("amountInvest")?.setFilterValue(newConditions);
              }}
            />

            {hasActiveFilters() && (
              <Button
                variant="ghost"
                onClick={() => table.resetColumnFilters()}
              >
                Reset <IconX />
              </Button>
            )}
          </div>

          <div className="rounded-md border">
            <Table>
              <TableHeader>
                {table.getHeaderGroups().map((headerGroup) => (
                  <TableRow key={headerGroup.id}>
                    {headerGroup.headers.map((header) => (
                      <TableHead key={header.id}>
                        {header.isPlaceholder
                          ? null
                          : flexRender(
                              header.column.columnDef.header,
                              header.getContext()
                            )}
                      </TableHead>
                    ))}
                  </TableRow>
                ))}
              </TableHeader>
              <TableBody>
                {table.getRowModel().rows?.length ? (
                  table.getRowModel().rows.map((row) => (
                    <TableRow
                      key={row.id}
                      data-state={row.getIsSelected() && "selected"}
                    >
                      {row.getVisibleCells().map((cell) => (
                        <TableCell key={cell.id}>
                          {flexRender(
                            cell.column.columnDef.cell,
                            cell.getContext()
                          )}
                        </TableCell>
                      ))}
                    </TableRow>
                  ))
                ) : (
                  <TableRow>
                    <TableCell
                      colSpan={columns.length}
                      className="h-24 text-center"
                    >
                      No results.
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </div>

          <div className="flex items-center justify-between py-4">
            <div className="text-muted-foreground text-sm">
              {table.getPaginationRowModel().rows.length} ligne(s) affichée(s)
            </div>

            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <span className="text-sm text-muted-foreground whitespace-nowrap">
                  Rows per page
                </span>
                <div className="relative">
                  <select
                    value={table.getState().pagination.pageSize}
                    onChange={(e) => table.setPageSize(Number(e.target.value))}
                    className="appearance-none border rounded px-2 py-1 text-sm bg-background text-foreground pr-6"
                  >
                    {[10, 15, 20, 25, 30].map((pageSize) => (
                      <option key={pageSize} value={pageSize}>
                        {pageSize}
                      </option>
                    ))}
                  </select>
                  <ChevronDown className="absolute right-1.5 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground pointer-events-none" />
                </div>
              </div>

              <span className="text-sm text-muted-foreground whitespace-nowrap">
                Page {table.getState().pagination.pageIndex + 1} of{" "}
                {table.getPageCount()}
              </span>

              <Pagination>
                <PaginationContent className="flex items-center space-x-2">
                  <PaginationItem>
                    <button
                      onClick={() => table.setPageIndex(0)}
                      disabled={!table.getCanPreviousPage()}
                      className="p-2 rounded hover:bg-accent disabled:opacity-50 disabled:pointer-events-none"
                    >
                      <ChevronsLeft className="h-4 w-4" />
                    </button>
                  </PaginationItem>

                  <PaginationItem>
                    <button
                      onClick={() => table.previousPage()}
                      disabled={!table.getCanPreviousPage()}
                      className="p-2 rounded hover:bg-accent disabled:opacity-50 disabled:pointer-events-none"
                    >
                      <ChevronLeft className="h-4 w-4" />
                    </button>
                  </PaginationItem>

                  <PaginationItem>
                    <button
                      onClick={() => table.nextPage()}
                      disabled={!table.getCanNextPage()}
                      className="p-2 rounded hover:bg-accent disabled:opacity-50 disabled:pointer-events-none"
                    >
                      <ChevronRight className="h-4 w-4" />
                    </button>
                  </PaginationItem>

                  <PaginationItem>
                    <button
                      onClick={() =>
                        table.setPageIndex(table.getPageCount() - 1)
                      }
                      disabled={!table.getCanNextPage()}
                      className="p-2 rounded hover:bg-accent disabled:opacity-50 disabled:pointer-events-none"
                    >
                      <ChevronsRight className="h-4 w-4" />
                    </button>
                  </PaginationItem>
                </PaginationContent>
              </Pagination>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
