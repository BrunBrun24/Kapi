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

import { Card, CardContent } from "@/components/ui/card";
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

import { TableDataPosition } from "@/components/analytics/titres/board/type";
import { IconAlertSquareRounded } from "@tabler/icons-react";
import { BoardTickerTransactionBuy } from "@/components/analytics/titres/board/positions/ticker/board-ticker-transaction-buy";

const data: TableDataPosition[] = [
  {
    ticker: "AAPL",
    name: "Apple Inc.",
    nbBuy: 3,
    logo: "https://logo.clearbit.com/apple.com",
    amountInvest: 4500,
    value: 4700,
    gains: 200,
    gainsPercentage: 4.44,
    gainsSP500: 180,
    gainsPercentageSP500: 4.0,
    difference: 20,
    durationDay: 365,
    annualizedPercentage: 4.44,
    capitalGainOrLoss: 150,
    capitalGainOrLossPercentage: 3.33,
    dividendAmount: 50,
    dividendYieldPercentage: 1.11,
    quantity: 25,
    fees: 10,
  },
  {
    ticker: "MSFT",
    name: "Microsoft Corp.",
    nbBuy: 2,
    logo: "https://logo.clearbit.com/microsoft.com",
    amountInvest: 3000,
    value: 3300,
    gains: 300,
    gainsPercentage: 10,
    gainsSP500: 250,
    gainsPercentageSP500: 8.33,
    difference: 50,
    durationDay: 200,
    annualizedPercentage: 18.25,
    capitalGainOrLoss: 270,
    capitalGainOrLossPercentage: 9,
    dividendAmount: 30,
    dividendYieldPercentage: 1,
    quantity: 15,
    fees: 5,
  },
  {
    ticker: "GOOGL",
    name: "Alphabet Inc.",
    nbBuy: 1,
    logo: "https://logo.clearbit.com/abc.xyz",
    amountInvest: 2500,
    value: 2600,
    gains: 100,
    gainsPercentage: 4,
    gainsSP500: 90,
    gainsPercentageSP500: 3.6,
    difference: 10,
    durationDay: 150,
    annualizedPercentage: 9.6,
    capitalGainOrLoss: 80,
    capitalGainOrLossPercentage: 3.2,
    dividendAmount: 0,
    dividendYieldPercentage: 0,
    quantity: 10,
    fees: 8,
  },
  {
    ticker: "TSLA",
    name: "Tesla Inc.",
    nbBuy: 4,
    logo: "https://logo.clearbit.com/tesla.com",
    amountInvest: 4000,
    value: 3800,
    gains: -200,
    gainsPercentage: -5,
    gainsSP500: -150,
    gainsPercentageSP500: -3.75,
    difference: -50,
    durationDay: 100,
    annualizedPercentage: -18,
    capitalGainOrLoss: -250,
    capitalGainOrLossPercentage: -6.25,
    dividendAmount: 0,
    dividendYieldPercentage: 0,
    quantity: 20,
    fees: 12,
  },
  {
    ticker: "AMZN",
    name: "Amazon.com Inc.",
    nbBuy: 2,
    logo: "https://logo.clearbit.com/amazon.com",
    amountInvest: 5000,
    value: 5400,
    gains: 400,
    gainsPercentage: 8,
    gainsSP500: 300,
    gainsPercentageSP500: 6,
    difference: 100,
    durationDay: 180,
    annualizedPercentage: 16.2,
    capitalGainOrLoss: 350,
    capitalGainOrLossPercentage: 7,
    dividendAmount: 50,
    dividendYieldPercentage: 1,
    quantity: 30,
    fees: 10,
  },
  {
    ticker: "NVDA",
    name: "NVIDIA Corp.",
    nbBuy: 3,
    logo: "https://logo.clearbit.com/nvidia.com",
    amountInvest: 6000,
    value: 7200,
    gains: 1200,
    gainsPercentage: 20,
    gainsSP500: 800,
    gainsPercentageSP500: 13.33,
    difference: 400,
    durationDay: 240,
    annualizedPercentage: 30.4,
    capitalGainOrLoss: 1100,
    capitalGainOrLossPercentage: 18.33,
    dividendAmount: 100,
    dividendYieldPercentage: 1.67,
    quantity: 40,
    fees: 15,
  },
  {
    ticker: "META",
    name: "Meta Platforms Inc.",
    nbBuy: 1,
    logo: "https://logo.clearbit.com/meta.com",
    amountInvest: 3500,
    value: 3400,
    gains: -100,
    gainsPercentage: -2.86,
    gainsSP500: -50,
    gainsPercentageSP500: -1.43,
    difference: -50,
    durationDay: 120,
    annualizedPercentage: -8.6,
    capitalGainOrLoss: -150,
    capitalGainOrLossPercentage: -4.29,
    dividendAmount: 0,
    dividendYieldPercentage: 0,
    quantity: 18,
    fees: 9,
  },
  {
    ticker: "JNJ",
    name: "Johnson & Johnson",
    nbBuy: 5,
    logo: "https://logo.clearbit.com/jnj.com",
    amountInvest: 2000,
    value: 2100,
    gains: 100,
    gainsPercentage: 5,
    gainsSP500: 80,
    gainsPercentageSP500: 4,
    difference: 20,
    durationDay: 90,
    annualizedPercentage: 21,
    capitalGainOrLoss: 90,
    capitalGainOrLossPercentage: 4.5,
    dividendAmount: 30,
    dividendYieldPercentage: 1.5,
    quantity: 22,
    fees: 4,
  },
  {
    ticker: "V",
    name: "Visa Inc.",
    nbBuy: 2,
    logo: "https://logo.clearbit.com/visa.com",
    amountInvest: 2800,
    value: 3000,
    gains: 200,
    gainsPercentage: 7.14,
    gainsSP500: 150,
    gainsPercentageSP500: 5.36,
    difference: 50,
    durationDay: 60,
    annualizedPercentage: 51,
    capitalGainOrLoss: 190,
    capitalGainOrLossPercentage: 6.79,
    dividendAmount: 10,
    dividendYieldPercentage: 0.36,
    quantity: 12,
    fees: 6,
  },
  {
    ticker: "KO",
    name: "Coca-Cola Co.",
    nbBuy: 4,
    logo: "https://logo.clearbit.com/coca-cola.com",
    amountInvest: 1500,
    value: 1550,
    gains: 50,
    gainsPercentage: 3.33,
    gainsSP500: 40,
    gainsPercentageSP500: 2.67,
    difference: 10,
    durationDay: 300,
    annualizedPercentage: 4.04,
    capitalGainOrLoss: 45,
    capitalGainOrLossPercentage: 3,
    dividendAmount: 25,
    dividendYieldPercentage: 1.67,
    quantity: 35,
    fees: 3,
  },
];

const columns: ColumnDef<TableDataPosition>[] = [
  {
    header: "Performance totale",
    columns: [
      {
        accessorKey: "ticker",
        header: "Ticker",
        cell: ({ row }) => {
          const { logo, name, ticker, nbBuy } = row.original;

          return (
            <div className="flex items-center gap-2 min-w-[180px]">
              <img
                src={logo}
                alt={ticker}
                className="w-8 h-8 rounded-full object-contain"
              />
              <div className="flex flex-col leading-tight text-left">
                <span className="font-medium text-sm">{name}</span>
                <span className="text-muted-foreground text-xs">
                  {ticker} / {nbBuy} achat{nbBuy > 1 ? "s" : ""}
                </span>
              </div>
            </div>
          );
        },
      },
      {
        accessorKey: "amountInvest",
        header: "Montant investi",
        cell: ({ getValue }) => `${getValue()} €`,
      },
      {
        accessorKey: "value",
        header: "Valeur",
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
              {value.toFixed(2)} €
            </span>
          );
        },
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
              {value.toFixed(2)} pts
            </span>
          );
        },
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
        cell: ({ getValue, row }) => {
          const value = parseFloat(getValue());
          const isPositive = value > 0;
          const duration = row.original.durationDay;
          const showWarning = duration < 365;

          const baseStyle =
            "px-2 py-1 rounded-full border text-xs font-medium inline-flex items-center gap-1";
          const style = isPositive
            ? "border-green-500 text-green-600"
            : "border-red-500 text-red-600";

          return (
            <span className={`${baseStyle} ${style}`}>
              {value.toFixed(2)} %
              {showWarning && (
                <IconAlertSquareRounded
                  size={17}
                  title="Attention : ce pourcentage est basé sur moins d’un an de détention. Il peut être trompeur et non représentatif d'une performance annualisée fiable."
                />
              )}
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
        accessorKey: "fees",
        header: "Frais",
        cell: ({ getValue }) => `${getValue()} €`,
      },
    ],
  },
];

export function BoardPositionsTickers() {
  const [sorting, setSorting] = React.useState<SortingState>([]);
  const [columnFilters, setColumnFilters] = React.useState<ColumnFiltersState>(
    []
  );
  const [columnVisibility, setColumnVisibility] =
    React.useState<VisibilityState>({});
  const [open, setOpen] = React.useState(false);
  const [selectedTicker, setSelectedTicker] = React.useState<string>("");

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

  const handleRowClick = (ticker: string) => {
    setSelectedTicker(ticker);
    setOpen(true);
  };

  // Indexs des colonnes où on veut un trait vertical (fin de bloc)
  const verticalBordersIndexes = [0, 1, 2, 4, 7, 9, 11];

  return (
    <>
      <div>
        <Card className="flex flex-col min-w-0">
          <CardContent>
            <div className="rounded-md border overflow-auto">
              <Table>
                <TableHeader>
                  {table.getHeaderGroups().map((headerGroup) => (
                    <TableRow key={headerGroup.id}>
                      {(() => {
                        let leafColumnIndex = 0; // compteur global de colonnes réelles

                        return headerGroup.headers.map((header) => {
                          const isLeaf = header.colSpan === 1;

                          // Vérifie si on est à une colonne à border
                          const shouldAddBorder = isLeaf
                            ? verticalBordersIndexes.includes(leafColumnIndex)
                            : verticalBordersIndexes.includes(
                                leafColumnIndex + header.colSpan - 1
                              );

                          const className = [
                            "text-center",
                            "bg-gray-50",
                            "min-w-[120px]",
                            shouldAddBorder ? "border-r border-gray-300" : "",
                            header.column.id === "ticker"
                              ? "sticky left-0 z-20 border-r border-gray-300"
                              : "",
                          ].join(" ");

                          // Incrémente l’index uniquement pour les colonnes réelles
                          if (isLeaf) {
                            leafColumnIndex += 1;
                          } else {
                            leafColumnIndex += header.colSpan;
                          }

                          return (
                            <TableHead
                              key={header.id}
                              colSpan={header.colSpan}
                              className={className}
                            >
                              {header.isPlaceholder
                                ? null
                                : flexRender(
                                    header.column.columnDef.header,
                                    header.getContext()
                                  )}
                            </TableHead>
                          );
                        });
                      })()}
                    </TableRow>
                  ))}
                </TableHeader>

                <TableBody>
                  {table.getRowModel().rows?.length ? (
                    table.getRowModel().rows.map((row) => (
                      <TableRow
                        key={row.id}
                        data-state={row.getIsSelected() && "selected"}
                        onClick={() => handleRowClick(row.original.ticker)}
                      >
                        {row.getVisibleCells().map((cell, i) => (
                          <TableCell
                            key={cell.id}
                            className={[
                              "text-center",
                              verticalBordersIndexes.includes(i)
                                ? "border-r border-gray-300"
                                : "",
                              i === 0 ? "sticky left-0 bg-white z-10" : "",
                            ].join(" ")}
                          >
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
              {/* Gauche : Nombre de lignes affichées */}
              <div className="text-muted-foreground text-sm">
                {table.getPaginationRowModel().rows.length} ligne(s) affichée(s)
              </div>

              {/* Droite : Sélecteur + Pagination */}
              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-2">
                  <span className="text-sm text-muted-foreground whitespace-nowrap">
                    Rows per page
                  </span>
                  <div className="relative">
                    <select
                      value={table.getState().pagination.pageSize}
                      onChange={(e) =>
                        table.setPageSize(Number(e.target.value))
                      }
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

      {open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 px-4 py-8 overflow-auto">
          <div className="rounded-lg shadow-lg p-6 w-auto max-w-full max-h-full overflow-auto">
            <BoardTickerTransactionBuy
              ticker={selectedTicker}
              setOpen={setOpen}
            />
          </div>
        </div>
      )}
    </>
  );
}
