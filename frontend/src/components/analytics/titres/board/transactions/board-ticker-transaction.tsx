"use client";

import {
  Pagination,
  PaginationContent,
  PaginationItem,
} from "@/components/ui/pagination";
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
import * as React from "react";

import api from "@/api";
import { TableDataTicker } from "@/components/analytics/titres/board/type";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  ArrowUpDown,
  ChevronLeft,
  ChevronRight,
  ChevronsLeft,
  ChevronsRight,
} from "lucide-react";
import { useEffect } from "react";
import { SelectedPortfolio } from "@/components/analytics/type";

function formatValueWithColor(
  value: number,
  options?: { suffix?: string; precision?: number }
) {
  const { suffix = "", precision = 2 } = options ?? {};
  const isPositive = value >= 0;

  const baseStyle =
    "px-2 py-1 rounded-full border text-xs font-medium inline-block";
  const style = isPositive
    ? "border-green-500 text-green-600"
    : "border-red-500 text-red-600";

  return (
    <span className={`${baseStyle} ${style}`}>
      {value.toFixed(precision)} {suffix}
    </span>
  );
}

const columns: ColumnDef<TableDataTicker>[] = [
  {
    header: "Informations",
    columns: [
      {
        accessorKey: "id",
        header: "#",
        cell: ({ getValue }) => (
          <div className="text-lg font-semibold px-1 text-center">
            {getValue()}
          </div>
        ),
      },
      {
        accessorKey: "ticker",
        header: "Ticker",
        cell: ({ row }) => {
          const logoUrl = row.original.logo;
          const companyName = "Name";
          const ticker = row.original.ticker;

          return (
            <div className="flex items-center gap-2">
              <img
                src={logoUrl}
                alt={ticker}
                className="w-8 h-8 rounded-full object-contain"
              />
              <div className="flex flex-col leading-tight text-left">
                <span className="font-medium text-sm">{companyName}</span>
                <span className="text-muted-foreground text-xs">{ticker}</span>
              </div>
            </div>
          );
        },
      },
      {
        accessorKey: "dateBuy",
        header: "Date",
        cell: ({ getValue }) =>
          new Date(getValue() as string).toLocaleDateString("fr-FR", {
            day: "numeric",
            month: "short",
            year: "numeric",
          }),
      },
      {
        accessorKey: "amount",
        header: "Achat",
        cell: ({ getValue }) => `${getValue()} €`,
      },
      {
        accessorKey: "stockValue",
        header: "Valeur ticker",
        cell: ({ getValue }) => `${getValue()} €`,
      },
    ],
  },
  {
    header: "Performances Totales",
    columns: [
      {
        accessorKey: "gains",
        header: ({ column }) => (
          <div className="relative flex justify-center items-center">
            <span>Gains</span>
            <button
              onClick={() =>
                column.toggleSorting(column.getIsSorted() === "asc")
              }
              className="absolute -bottom-5 z-10 w-5 h-5 rounded-full border bg-background hover:bg-accent flex items-center justify-center shadow"
              title="Trier par date"
            >
              <ArrowUpDown className="w-3.5 h-3.5" />
            </button>
          </div>
        ),
        cell: ({ getValue }) =>
          formatValueWithColor(parseFloat(getValue()), { suffix: "€" }),
      },
      {
        accessorKey: "gainsPercentage",
        header: ({ column }) => (
          <div className="relative flex justify-center items-center">
            <span>Gains %</span>
            <button
              onClick={() =>
                column.toggleSorting(column.getIsSorted() === "asc")
              }
              className="absolute -bottom-5 z-10 w-5 h-5 rounded-full border bg-background hover:bg-accent flex items-center justify-center shadow"
              title="Trier par date"
            >
              <ArrowUpDown className="w-3.5 h-3.5" />
            </button>
          </div>
        ),
        cell: ({ getValue }) =>
          formatValueWithColor(parseFloat(getValue()), { suffix: "%" }),
      },
    ],
  },
  {
    header: "VS S&P500",
    columns: [
      {
        accessorKey: "gainsSP500",
        header: "S&P",
        cell: ({ getValue }) => `${getValue()} €`,
      },
      {
        accessorKey: "gainsPercentageSP500",
        header: "S&P %",
        cell: ({ getValue }) => `${getValue()} %`,
      },
      {
        accessorKey: "difference",
        header: ({ column }) => (
          <div className="relative flex justify-center items-center">
            <span>Écart</span>
            <button
              onClick={() =>
                column.toggleSorting(column.getIsSorted() === "asc")
              }
              className="absolute -bottom-5 z-10 w-5 h-5 rounded-full border bg-background hover:bg-accent flex items-center justify-center shadow"
              title="Trier par date"
            >
              <ArrowUpDown className="w-3.5 h-3.5" />
            </button>
          </div>
        ),
        cell: ({ getValue }) =>
          formatValueWithColor(parseFloat(getValue()), { suffix: "pts" }),
      },
    ],
  },
  {
    header: "Temps",
    columns: [
      {
        accessorKey: "durationDay",
        header: "Durée",
        cell: ({ getValue }) => `${getValue()} jours`,
      },
      {
        accessorKey: "annualizedPercentage",
        header: ({ column }) => (
          <div className="relative flex justify-center items-center">
            <span>% an</span>
            <button
              onClick={() =>
                column.toggleSorting(column.getIsSorted() === "asc")
              }
              className="absolute -bottom-5 z-10 w-5 h-5 rounded-full border bg-background hover:bg-accent flex items-center justify-center shadow"
              title="Trier par date"
            >
              <ArrowUpDown className="w-3.5 h-3.5" />
            </button>
          </div>
        ),
        cell: ({ getValue }) => {
          const value = parseFloat(getValue());
          const isPositive = value > 0;
          const baseStyle =
            "px-2 py-1 rounded-full border text-xs font-medium inline-block";
          const style = isPositive
            ? "border-green-500 text-green-600"
            : "border-red-500 text-red-600";

          return (
            <span className={`${baseStyle} ${style}`}>
              {value.toFixed(2)} %
            </span>
          );
        },
      },
    ],
  },
  {
    header: "Dividendes",
    columns: [
      {
        accessorKey: "dividendAmount",
        header: "Montant",
        cell: ({ getValue }) => `${getValue()} €`,
      },
      {
        accessorKey: "dividendYieldPercentage",
        header: "Rendement",
        cell: ({ getValue }) => `${getValue()} %`,
      },
    ],
  },
  {
    header: "Détails",
    columns: [
      {
        accessorKey: "quantity",
        header: "Quantité",
      },
      {
        accessorKey: "pru",
        header: "PRU",
        cell: ({ getValue }) => `${getValue()} €`,
      },
      {
        accessorKey: "fees",
        header: "Frais",
        cell: ({ getValue }) => `${getValue()} €`,
      },
    ],
  },
];

const stickyColumnIndexes = [0, 1, 2];
const stickyStyles = [
  { left: 0, width: 50 },
  { left: 50, width: 200 },
  { left: 250, width: 130 },
];
const verticalBordersIndexes = [0, 1, 2, 4, 6, 9, 11, 13, 16];

export function BoardAllTransactions({ selectedPortfolio }: SelectedPortfolio) {
  const [sorting, setSorting] = React.useState<SortingState>([]);
  const [columnFilters, setColumnFilters] = React.useState<ColumnFiltersState>(
    []
  );
  const [columnVisibility, setColumnVisibility] =
    React.useState<VisibilityState>({});
  const [performances, setPerformances] = React.useState<any[]>([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await api.get(
          `/api/portfolio-performance/all-ticker-transactions/${selectedPortfolio.id}/`
        );
        setPerformances(res.data);
      } catch (error) {
        console.error("Error fetching performance data:", error);
      }
    };

    fetchData();
  }, [selectedPortfolio]);

  const table = useReactTable({
    data: performances,
    columns,
    state: { sorting, columnFilters, columnVisibility },
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    onColumnVisibilityChange: setColumnVisibility,
    getCoreRowModel: getCoreRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    initialState: { pagination: { pageSize: 10 } },
  });

  return (
    <div className="w-full overflow-auto">
      <Card className="flex flex-col">
        <CardContent>
          <div className="rounded-md border overflow-auto">
            <Table>
              <TableHeader>
                {table.getHeaderGroups().map((headerGroup) => {
                  let leafColumnIndex = 0;
                  return (
                    <TableRow key={headerGroup.id}>
                      {headerGroup.headers.map((header) => {
                        const isLeaf = header.colSpan === 1;
                        const indexForBorder = isLeaf
                          ? leafColumnIndex
                          : leafColumnIndex + header.colSpan - 1;
                        const stickyIndex =
                          stickyColumnIndexes.indexOf(leafColumnIndex);
                        const isSticky = stickyIndex !== -1;
                        const shouldAddBorder =
                          verticalBordersIndexes.includes(indexForBorder);

                        let className = [
                          "text-center",
                          "bg-gray-50",
                          "min-w-[120px]",
                          shouldAddBorder ? "border-r border-gray-300" : "",
                        ].join(" ");

                        if (isSticky && isLeaf) className += " sticky z-20";

                        const style =
                          isSticky && isLeaf
                            ? ({
                                position: "sticky",
                                left: stickyStyles[stickyIndex].left,
                                minWidth: stickyStyles[stickyIndex].width,
                                maxWidth: stickyStyles[stickyIndex].width,
                              } as React.CSSProperties)
                            : undefined;

                        leafColumnIndex += header.colSpan;

                        return (
                          <TableHead
                            key={header.id}
                            colSpan={header.colSpan}
                            className={className}
                            style={style}
                          >
                            {header.isPlaceholder
                              ? null
                              : flexRender(
                                  header.column.columnDef.header,
                                  header.getContext()
                                )}
                          </TableHead>
                        );
                      })}
                    </TableRow>
                  );
                })}
              </TableHeader>

              <TableBody>
                {table.getRowModel().rows.length > 0 ? (
                  table.getRowModel().rows.map((row) => {
                    let cellIndex = 0;
                    return (
                      <TableRow key={row.id}>
                        {row.getVisibleCells().map((cell) => {
                          const stickyIndex =
                            stickyColumnIndexes.indexOf(cellIndex);
                          const isSticky = stickyIndex !== -1;
                          const shouldAddBorder =
                            verticalBordersIndexes.includes(cellIndex);

                          let className = [
                            "text-center",
                            shouldAddBorder ? "border-r border-gray-300" : "",
                          ].join(" ");
                          if (isSticky) className += " sticky bg-white z-20";

                          const style = isSticky
                            ? ({
                                position: "sticky",
                                left: stickyStyles[stickyIndex].left,
                                minWidth: stickyStyles[stickyIndex].width,
                                maxWidth: stickyStyles[stickyIndex].width,
                                backgroundColor: "white",
                              } as React.CSSProperties)
                            : {};

                          cellIndex++;

                          return (
                            <TableCell
                              key={cell.id}
                              className={className}
                              style={style}
                            >
                              {flexRender(
                                cell.column.columnDef.cell,
                                cell.getContext()
                              )}
                            </TableCell>
                          );
                        })}
                      </TableRow>
                    );
                  })
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

            <div className="flex items-center justify-between py-4">
              <div className="text-muted-foreground text-sm">
                {table.getPaginationRowModel().rows.length} ligne(s) affichée(s)
              </div>

              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-2">
                  <span
                    className="text-sm text-muted-foreground whitespace-nowrap"
                    id="rows-per-page-label"
                  >
                    Rows per page
                  </span>

                  <Select
                    value={String(table.getState().pagination.pageSize)}
                    onValueChange={(value) => table.setPageSize(Number(value))}
                  >
                    <SelectTrigger
                      className="w-[80px]"
                      aria-labelledby="rows-per-page-label"
                    >
                      <SelectValue placeholder="Select rows" />
                    </SelectTrigger>

                    <SelectContent>
                      {[10, 15, 20, 25, 30].map((pageSize) => (
                        <SelectItem key={pageSize} value={String(pageSize)}>
                          {pageSize}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <span className="text-sm text-muted-foreground whitespace-nowrap">
                  Page {table.getState().pagination.pageIndex + 1} of{" "}
                  {table.getPageCount()}
                </span>

                <Pagination>
                  <PaginationContent className="flex items-center space-x-2">
                    <PaginationItem>
                      <Button
                        variant="outline"
                        size="icon"
                        onClick={() => table.setPageIndex(0)}
                        disabled={!table.getCanPreviousPage()}
                        aria-label="Première page"
                      >
                        <ChevronsLeft className="w-4 h-4" />
                      </Button>
                    </PaginationItem>

                    <PaginationItem>
                      <Button
                        variant="outline"
                        size="icon"
                        onClick={() => table.previousPage()}
                        disabled={!table.getCanPreviousPage()}
                        aria-label="Page précédente"
                      >
                        <ChevronLeft className="w-4 h-4" />
                      </Button>
                    </PaginationItem>

                    <PaginationItem>
                      <Button
                        variant="outline"
                        size="icon"
                        onClick={() => table.nextPage()}
                        disabled={!table.getCanNextPage()}
                        aria-label="Page suivante"
                      >
                        <ChevronRight className="w-4 h-4" />
                      </Button>
                    </PaginationItem>

                    <PaginationItem>
                      <Button
                        variant="outline"
                        size="icon"
                        onClick={() =>
                          table.setPageIndex(table.getPageCount() - 1)
                        }
                        disabled={!table.getCanNextPage()}
                        aria-label="Dernière page"
                      >
                        <ChevronsRight className="w-4 h-4" />
                      </Button>
                    </PaginationItem>
                  </PaginationContent>
                </Pagination>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
