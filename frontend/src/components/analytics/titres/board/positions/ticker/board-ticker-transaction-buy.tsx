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

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
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
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  ChevronsLeft,
  ChevronsRight,
} from "lucide-react";
import { Dialog, DialogContent } from "@/components/ui/dialog";
import { TableDataTicker } from "@/components/analytics/titres/board/type";

const data: TableDataTicker[] = [
  {
    id: 1,
    ticker: "INTU",
    dateBuy: new Date("2023-03-15"),
    amount: 5000,
    stockValue: 5600,
    gains: 600,
    gainsPercentage: 12,
    gainsSP500: 450,
    gainsPercentageSP500: 9,
    difference: 150,
    durationDay: 365,
    annualizedPercentage: 12.0,
    capitalGainOrLoss: 580,
    capitalGainOrLossPercentage: 11.6,
    dividendAmount: 20,
    dividendYieldPercentage: 0.4,
    quantity: 50,
    pru: 100,
    fees: 10,
  },
  {
    id: 2,
    ticker: "INTU",
    dateBuy: new Date("2022-11-10"),
    amount: 3000,
    stockValue: 3300,
    gains: 300,
    gainsPercentage: 10,
    gainsSP500: 250,
    gainsPercentageSP500: 8.3,
    difference: 50,
    durationDay: 570,
    annualizedPercentage: 6.2,
    capitalGainOrLoss: 290,
    capitalGainOrLossPercentage: 9.7,
    dividendAmount: 10,
    dividendYieldPercentage: 0.33,
    quantity: 30,
    pru: 100,
    fees: 5,
  },
  {
    id: 3,
    ticker: "INTU",
    dateBuy: new Date("2021-01-25"),
    amount: 4000,
    stockValue: 5200,
    gains: 1200,
    gainsPercentage: 30,
    gainsSP500: 800,
    gainsPercentageSP500: 20,
    difference: 400,
    durationDay: 1225,
    annualizedPercentage: 8.2,
    capitalGainOrLoss: 1100,
    capitalGainOrLossPercentage: 27.5,
    dividendAmount: 100,
    dividendYieldPercentage: 2.5,
    quantity: 40,
    pru: 100,
    fees: 10,
  },
];

function formatValueWithColor(
  value: number,
  options?: {
    suffix?: string;
    precision?: number;
  }
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
          const logoUrl = "Logo";
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
        header: ({ column }) => (
          <div className="relative flex justify-center items-center">
            <span>Date</span>
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

// Index des colonnes sticky (id, ticker, dateBuy)
const stickyColumnIndexes = [0, 1, 2];

// Largeurs fixes pour les colonnes sticky (en px)
const stickyStyles = [
  { left: 0, width: 50 }, // id
  { left: 50, width: 200 }, // ticker
  { left: 250, width: 130 }, // dateBuy
];

// Vertical borders index restent inchangés
const verticalBordersIndexes = [0, 1, 2, 4, 6, 9, 11, 13, 16];

export function BoardTickerTransactionBuy({
  ticker,
  setOpen,
}: {
  ticker: string;
  setOpen: (value: boolean) => void;
}) {
  const [sorting, setSorting] = React.useState<SortingState>([]);
  const [columnFilters, setColumnFilters] = React.useState<ColumnFiltersState>(
    []
  );
  const [columnVisibility, setColumnVisibility] =
    React.useState<VisibilityState>({});

  const table = useReactTable({
    data,
    columns,
    state: {
      sorting,
      columnFilters,
      columnVisibility,
    },
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    onColumnVisibilityChange: setColumnVisibility,
    getCoreRowModel: getCoreRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    initialState: {
      pagination: {
        pageSize: 10,
      },
    },
  });

  return (
    <div className="w-full overflow-auto">
      <Card className="flex flex-col">
        <CardHeader className="pb-2">
          <div className="flex justify-between items-start">
            <div>
              <CardTitle className="text-2xl font-bold">
                Transactions d'achat - {ticker}
              </CardTitle>
              <CardDescription>
                Toutes les transactions d'achat liées à la position ouverte de
                votre titre {ticker}
              </CardDescription>
            </div>
            <button
              onClick={() => setOpen(false)}
              className="text-gray-500 hover:text-black text-2xl font-bold leading-none"
              aria-label="Fermer"
            >
              &times;
            </button>
          </div>
        </CardHeader>

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

                        // Détection si la colonne est sticky
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

                        // Override largeur et sticky si colonne sticky
                        if (isSticky && isLeaf) {
                          className += " sticky z-20";
                        }

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

                          if (isSticky) {
                            className += " sticky bg-white z-20";
                          }

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
                      <ChevronsLeft className="w-4 h-4" />
                    </button>
                  </PaginationItem>
                  <PaginationItem>
                    <button
                      onClick={() => table.previousPage()}
                      disabled={!table.getCanPreviousPage()}
                      className="p-2 rounded hover:bg-accent disabled:opacity-50 disabled:pointer-events-none"
                    >
                      <ChevronLeft className="w-4 h-4" />
                    </button>
                  </PaginationItem>

                  <PaginationItem>
                    <button
                      onClick={() => table.nextPage()}
                      disabled={!table.getCanNextPage()}
                      className="p-2 rounded hover:bg-accent disabled:opacity-50 disabled:pointer-events-none"
                    >
                      <ChevronRight className="w-4 h-4" />
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
                      <ChevronsRight className="w-4 h-4" />
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
