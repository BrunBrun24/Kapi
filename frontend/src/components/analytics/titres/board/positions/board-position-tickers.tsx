"use client";

import {
  ColumnDef,
  ColumnFiltersState,
  flexRender,
  getCoreRowModel,
  getFilteredRowModel,
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
import { ArrowUpDown } from "lucide-react";

import api from "@/api";
import { BoardTickerTransactionBuy } from "@/components/analytics/titres/board/positions/ticker/board-ticker-transaction-buy";
import { TableDataPosition } from "@/components/analytics/titres/board/type";
import { SelectedPortfolio } from "@/components/analytics/type";
import { IconAlertSquareRounded } from "@tabler/icons-react";
import { useEffect } from "react";

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
            <div className="flex items-center gap-2 min-w-[180px] max-w-[220px]">
              <img
                src={logo}
                alt={ticker}
                className="w-8 h-8 rounded-full object-contain shrink-0"
              />
              <div className="flex flex-col leading-tight text-left overflow-hidden">
                <span
                  className="font-medium text-sm truncate max-w-[160px]"
                  title={name} // Affiche le nom complet au survol
                >
                  {name}
                </span>
                <span className="text-muted-foreground text-xs truncate">
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
        cell: ({ getValue, row }) => `${getValue()} ${row.original.currency}`,
      },
      {
        accessorKey: "value",
        header: "Valeur",
        cell: ({ getValue, row }) => `${getValue()} ${row.original.currency}`,
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
        cell: ({ getValue, row }) => {
          const value = parseFloat(getValue());
          const isPositive = value > 0;
          const baseStyle =
            "px-2 py-1 rounded-full border text-xs font-medium inline-block";
          const style = isPositive
            ? "border-green-500 text-green-600"
            : "border-red-500 text-red-600";

          return (
            <span className={`${baseStyle} ${style}`}>
              {value.toFixed(2)} {row.original.currency}
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
        cell: ({ getValue, row }) => `${getValue()} ${row.original.currency}`,
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
        cell: ({ getValue, row }) => `${getValue()} ${row.original.currency}`,
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
        cell: ({ getValue, row }) => `${getValue()} ${row.original.currency}`,
      },
    ],
  },
];

export function BoardPositionsTickers({
  selectedPortfolio,
}: SelectedPortfolio) {
  const [sorting, setSorting] = React.useState<SortingState>([]);
  const [columnFilters, setColumnFilters] = React.useState<ColumnFiltersState>(
    []
  );
  const [columnVisibility, setColumnVisibility] =
    React.useState<VisibilityState>({});
  const [open, setOpen] = React.useState(false);
  const [selectedTicker, setSelectedTicker] = React.useState<string>("");
  const [performances, setPerformances] = React.useState<any[]>([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await api.get(
          `/api/portfolio-performance/tickers-performances/${selectedPortfolio.id}/`
        );
        setPerformances(res.data);
      } catch (error) {
        console.error("Error fetching performance data:", error);
      }
    };

    fetchData();
  }, [selectedPortfolio]);

  const handleRowClick = (ticker: string) => {
    setSelectedTicker(ticker);
    setOpen(true);
  };

  const table = useReactTable({
    data: performances,
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
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
  });

  const verticalBordersIndexes = [0, 1, 2, 4, 7, 9, 11];

  return (
    <>
      <Card className="flex flex-col min-w-0">
        <CardContent>
          <div className="rounded-md border overflow-x-auto overflow-y-auto max-h-[600px] w-full">
            <Table>
              <TableHeader>
                {table.getHeaderGroups().map((headerGroup) => (
                  <TableRow key={headerGroup.id}>
                    {(() => {
                      let leafColumnIndex = 0;
                      return headerGroup.headers.map((header) => {
                        const isLeaf = header.colSpan === 1;
                        const shouldAddBorder = isLeaf
                          ? verticalBordersIndexes.includes(leafColumnIndex)
                          : verticalBordersIndexes.includes(
                              leafColumnIndex + header.colSpan - 1
                            );

                        const className = [
                          "text-center bg-gray-50 min-w-[120px]",
                          shouldAddBorder ? "border-r border-gray-300" : "",
                          header.column.id === "ticker"
                            ? "sticky left-0 z-20 border-r border-gray-300"
                            : "",
                        ].join(" ");

                        if (isLeaf) leafColumnIndex += 1;
                        else leafColumnIndex += header.colSpan;

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
                {table.getRowModel().rows.length ? (
                  table.getRowModel().rows.map((row) => (
                    <TableRow
                      key={row.id}
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
        </CardContent>
      </Card>

      {open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 px-4 py-8 overflow-auto">
          <div className="rounded-lg shadow-lg p-6 w-auto max-w-full max-h-full overflow-auto">
            <BoardTickerTransactionBuy
              ticker={selectedTicker}
              setOpen={setOpen}
              selectedPortfolio={selectedPortfolio}
            />
          </div>
        </div>
      )}
    </>
  );
}
