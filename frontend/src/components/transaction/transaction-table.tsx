import React, { useEffect, useState } from "react";
import {
  Edit,
  Trash2,
  MoveRight,
  MoveLeft,
  Percent,
  ShoppingCart,
  BanknoteArrowDown,
  BanknoteArrowUp,
  Banknote,
  Handshake,
} from "lucide-react";
import {
  Pagination,
  PaginationContent,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from "@/components/ui/pagination";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "../ui/alert-dialog";

import api from "@/api";
import TransactionFilter from "./transaction-filter";
import type { Ticker, Transaction } from "@/components/transaction/type/index";

import "@/static/css/components/transaction/transaction-table.css";

interface TransactionTableProps {
  selectedPortfolioId: string;
  onEdit: (transaction: Transaction) => void;
  refreshKey: number;
  onRefresh: () => void;
  tickersInPortfolio: Ticker[];
}

const TransactionTable: React.FC<TransactionTableProps> = ({
  selectedPortfolioId,
  onEdit,
  refreshKey,
  onRefresh,
  tickersInPortfolio,
}) => {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [currencySymbols, setCurrencySymbols] = useState<{
    [ticker: string]: string;
  }>({});

  // Pagination
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 13;

  // Filtre
  const [filters, setFilters] = useState<
    Partial<Record<keyof Transaction, string[]>>
  >({});
  const [sortOrders, setSortOrders] = useState<
    Partial<Record<keyof Transaction, "asc" | "desc">>
  >({});
  const [openedFilter, setOpenedFilter] = useState<keyof Transaction | null>(
    null
  );

  const operationConfig = {
    buy: { icon: <ShoppingCart size={15} />, label: "Achat" },
    sell: { icon: <Handshake size={15} />, label: "Vente" },
    dividend: { icon: <Banknote size={15} />, label: "Dividende" },
    interest: { icon: <Percent size={15} />, label: "Intérêt" },
    deposit: {
      icon: <BanknoteArrowDown size={15} />,
      label: "Rentrer d'argent",
    },
    withdrawal: {
      icon: <BanknoteArrowUp size={15} />,
      label: "Sortie d'argent",
    },
  };

  // Suppression
  const [transactionToDelete, setTransactionToDelete] =
    useState<Transaction | null>(null);

  const updateFilter = (column: keyof Transaction, values?: string[]) => {
    setFilters((prev) => {
      const defaultValues = values ?? getFilterOptions(column).slice(0, 15);
      return {
        ...prev,
        [column]: defaultValues,
      };
    });
    setCurrentPage(1);
  };

  const getFilteredTransactions = (): Transaction[] => {
    const filtered = transactions.filter((tx) => {
      return Object.entries(filters).every(([key, values]) => {
        const column = key as keyof Transaction;
        return !values.length || values.includes(String(tx[column]));
      });
    });

    const sortableColumns = Object.keys(sortOrders) as (keyof Transaction)[];
    const columnToSort = sortableColumns.find((col) => sortOrders[col]);
    const sortOrder = columnToSort ? sortOrders[columnToSort] : undefined;

    if (columnToSort && sortOrder) {
      return [...filtered].sort((a, b) => {
        const aVal = a[columnToSort];
        const bVal = b[columnToSort];

        // Sécurité : fallback vide si undefined/null
        const aStr = aVal != null ? String(aVal) : "";
        const bStr = bVal != null ? String(bVal) : "";

        // Tri spécial pour les dates
        if (columnToSort === "date") {
          const aDate = new Date(aStr).getTime();
          const bDate = new Date(bStr).getTime();
          return sortOrder === "asc" ? aDate - bDate : bDate - aDate;
        }

        // Tri numérique si applicable
        const aNum = Number(aStr);
        const bNum = Number(bStr);
        if (!isNaN(aNum) && !isNaN(bNum)) {
          return sortOrder === "asc" ? aNum - bNum : bNum - aNum;
        }

        // Sinon tri alphabétique (ticker, operation, etc.)
        return sortOrder === "asc"
          ? aStr.localeCompare(bStr)
          : bStr.localeCompare(aStr);
      });
    }

    return filtered;
  };

  const filteredTransactions = getFilteredTransactions();
  const totalPages = Math.max(
    1,
    Math.ceil(filteredTransactions.length / itemsPerPage)
  );

  useEffect(() => {
    if (currentPage > totalPages) {
      setCurrentPage(totalPages);
    }
  }, [currentPage, totalPages]);

  const handleSortChange = (
    column: keyof Transaction,
    order: "asc" | "desc" | null
  ) => {
    if (order) {
      setSortOrders({ [column]: order }); // ❗ remplace complètement l'objet
    } else {
      setSortOrders({});
    }
  };

  const getFilterOptions = (column: keyof Transaction): string[] => {
    const filteredForOptions = transactions.filter((tx) =>
      Object.entries(filters).every(([key, values]) => {
        if (key === column) return true; // ignore current column
        return (
          !values.length ||
          values.includes(String(tx[key as keyof Transaction]))
        );
      })
    );

    const uniqueValues = Array.from(
      new Set(filteredForOptions.map((tx) => String(tx[column])))
    );

    // Détermine le type pour le tri
    if (["quantity", "amount", "fees", "stock_price"].includes(column)) {
      // Tri numérique
      return uniqueValues
        .map((val) => Number(val))
        .filter((n) => !isNaN(n))
        .sort((a, b) => a - b)
        .map((n) => String(n));
    }

    if (column === "date") {
      // Tri chronologique récent -> ancien
      return uniqueValues.sort(
        (a, b) => new Date(b).getTime() - new Date(a).getTime()
      );
    }

    // Tri alphabétique par défaut
    return uniqueValues.sort((a, b) => a.localeCompare(b));
  };

  useEffect(() => {
    if (!selectedPortfolioId) return;

    const fetchTransactions = async () => {
      try {
        const response = await api.get(
          `/api/portfolio-transaction/${selectedPortfolioId}`
        );
        setTransactions(response.data);
      } catch (error) {
        console.error("Erreur lors du chargement des transactions :", error);
      }
    };

    fetchTransactions();
  }, [selectedPortfolioId, refreshKey]);

  useEffect(() => {
    const handleCurrency = async () => {
      try {
        const response = await api.get(`/api/ticker/currency/`, {
          params: {
            portfolio_id: selectedPortfolioId,
          },
        });
        setCurrencySymbols(response.data);
      } catch (error) {
        console.error("Erreur lors du chargement du symbole :", error);
      }
    };

    if (selectedPortfolioId) {
      handleCurrency();
    }
  }, [selectedPortfolioId]);

  const confirmDeleteTransaction = async () => {
    if (!transactionToDelete) return;

    try {
      await api.delete(
        `api/portfolio-transaction/${transactionToDelete.id}/delete`
      );
      onRefresh();
    } catch (error) {
      console.error("Erreur lors de la suppression de la transaction", error);
      // Tu peux ajouter un toast ici
    } finally {
      setTransactionToDelete(null);
    }
  };

  const paginatedTransactions = filteredTransactions.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );

  const formatNumberWithSymbol = (value: number, symbol: string): string => {
    if (value === null || isNaN(value)) return "-";

    const absValue = Math.abs(value);

    let formatted: string;
    if (absValue >= 1_000_000_000) {
      formatted = (value / 1_000_000_000).toFixed(2).replace(/\.00$/, "") + "B";
    } else if (absValue >= 1_000_000) {
      formatted = (value / 1_000_000).toFixed(2).replace(/\.00$/, "") + "M";
    } else if (absValue >= 1_000) {
      formatted = (value / 1_000).toFixed(2).replace(/\.00$/, "") + "k";
    } else {
      formatted = value.toFixed(2).replace(/\.00$/, "");
    }

    // Si c’est abrégé (lettre en fin), on ne met pas le symbole
    return /[kMB]$/.test(formatted) ? formatted : `${formatted} ${symbol}`;
  };

  const handlePrevious = () => {
    if (currentPage > 1) setCurrentPage(currentPage - 1);
  };

  const handleNext = () => {
    if (currentPage < totalPages) setCurrentPage(currentPage + 1);
  };

  const getPageNumbers = () => {
    const pages = [];

    const maxVisible = 3;
    const start = Math.max(1, currentPage - Math.floor(maxVisible / 2));
    const end = Math.min(totalPages, start + maxVisible - 1);

    // Ajout de la première page
    if (start > 1) {
      pages.push(1);
      if (start > 2) pages.push("ellipsis-left");
    }

    for (let i = start; i <= end; i++) {
      pages.push(i);
    }

    // Ajout de la dernière page
    if (end < totalPages) {
      if (end < totalPages - 1) pages.push("ellipsis-right");
      pages.push(totalPages);
    }

    return pages;
  };

  const pages = getPageNumbers();

  return (
    <div>
      <div className="table_wrapper">
        <div style={{ minHeight: 495, maxHeight: 785, overflowY: "auto" }}>
          <table className="table">
            <thead>
              <tr className="header_row">
                <th>
                  <div className="sort_button">
                    Date
                    <TransactionFilter
                      column="date"
                      options={getFilterOptions("date")}
                      selectedValues={
                        filters["date"] ?? getFilterOptions("date")
                      }
                      onChange={(values) => updateFilter("date", values)}
                      onSortChange={(order) => handleSortChange("date", order)}
                      openedFilter={openedFilter}
                      setOpenedFilter={setOpenedFilter}
                    />
                  </div>
                </th>
                <th>
                  <div className="sort_button">
                    Type
                    <TransactionFilter
                      column="operation"
                      options={getFilterOptions("operation")}
                      selectedValues={
                        filters["operation"] ?? getFilterOptions("operation")
                      }
                      onChange={(values) => updateFilter("operation", values)}
                      onSortChange={(order) =>
                        handleSortChange("operation", order)
                      }
                      openedFilter={openedFilter}
                      setOpenedFilter={setOpenedFilter}
                    />
                  </div>
                </th>
                <th>
                  <div className="sort_button">
                    Ticker
                    <TransactionFilter
                      column="ticker"
                      options={getFilterOptions("ticker")}
                      selectedValues={
                        filters["ticker"] ?? getFilterOptions("ticker")
                      }
                      onChange={(values) => updateFilter("ticker", values)}
                      onSortChange={(order) =>
                        handleSortChange("ticker", order)
                      }
                      openedFilter={openedFilter}
                      setOpenedFilter={setOpenedFilter}
                    />
                  </div>
                </th>
                <th>
                  <div className="sort_button">
                    Quantités
                    <TransactionFilter
                      column="quantity"
                      options={getFilterOptions("quantity")}
                      selectedValues={
                        filters["quantity"] ?? getFilterOptions("quantity")
                      }
                      onChange={(values) => updateFilter("quantity", values)}
                      onSortChange={(order) =>
                        handleSortChange("quantity", order)
                      }
                      openedFilter={openedFilter}
                      setOpenedFilter={setOpenedFilter}
                    />
                  </div>
                </th>
                <th>
                  <div className="sort_button">
                    Prix
                    <TransactionFilter
                      column="amount"
                      options={getFilterOptions("amount")}
                      selectedValues={
                        filters["amount"] ?? getFilterOptions("amount")
                      }
                      onChange={(values) => updateFilter("amount", values)}
                      onSortChange={(order) =>
                        handleSortChange("amount", order)
                      }
                      openedFilter={openedFilter}
                      setOpenedFilter={setOpenedFilter}
                    />
                  </div>
                </th>
                <th>Prix d'achat</th>
                <th>
                  <div className="sort_button">
                    Frais
                    <TransactionFilter
                      column="fees"
                      options={getFilterOptions("fees")}
                      selectedValues={
                        filters["fees"] ?? getFilterOptions("fees")
                      }
                      onChange={(values) => updateFilter("fees", values)}
                      onSortChange={(order) => handleSortChange("fees", order)}
                      openedFilter={openedFilter}
                      setOpenedFilter={setOpenedFilter}
                    />
                  </div>
                </th>
                <th>Total</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {paginatedTransactions.map((transaction) => {
                const tickerInfo = tickersInPortfolio.find(
                  (t) => t.ticker === transaction.ticker
                );

                return (
                  <tr key={transaction.id} className="body_row">
                    <td className="date">
                      {new Date(transaction.date)
                        .toLocaleDateString("fr-CA")
                        .replace(/-/g, "/")}
                    </td>
                    <td>
                      <span className="type">
                        {operationConfig[transaction.operation]?.icon}
                        {operationConfig[transaction.operation]?.label}
                      </span>
                    </td>
                    <td className="ticker">
                      {transaction.ticker !== "" && tickerInfo ? (
                        <>
                          <img
                            src={tickerInfo.logo}
                            alt={`Logo de ${tickerInfo.ticker}`}
                            className="tab-ticker-logo"
                          />
                          {tickerInfo.ticker}
                        </>
                      ) : (
                        "-"
                      )}
                    </td>
                    <td className="numeric">
                      {transaction.quantity !== 0 &&
                      transaction.quantity != null
                        ? transaction.quantity
                        : "-"}
                    </td>
                    <td className="numeric">
                      {transaction.amount !== 0 && transaction.amount != null
                        ? formatNumberWithSymbol(
                            transaction.amount,
                            currencySymbols[transaction.ticker] ||
                              transaction.currency
                          )
                        : "-"}
                    </td>
                    <td className="numeric">
                      {transaction.stock_price !== 0 &&
                      transaction.stock_price != null
                        ? `${transaction.stock_price} ${
                            currencySymbols[transaction.ticker] || ""
                          }`
                        : "-"}
                    </td>
                    <td className="numeric">
                      {transaction.fees !== 0
                        ? formatNumberWithSymbol(
                            transaction.fees,
                            currencySymbols[transaction.ticker] ||
                              transaction.currency
                          )
                        : "-"}
                    </td>
                    <td
                      className={`numeric ${
                        transaction.operation === "withdrawal"
                          ? "negatif"
                          : transaction.amount - (transaction.fees || 0) > 0
                          ? "positive"
                          : transaction.amount - (transaction.fees || 0) < 0
                          ? "negatif"
                          : ""
                      }`}
                    >
                      {(() => {
                        const amount =
                          transaction.operation === "withdrawal"
                            ? -transaction.amount
                            : transaction.amount;

                        const netAmount = amount - (transaction.fees || 0);

                        const symbol =
                          transaction.operation === "withdrawal"
                            ? ""
                            : transaction.amount - (transaction.fees || 0) > 0
                            ? "+"
                            : "";

                        return (
                          symbol +
                          formatNumberWithSymbol(
                            netAmount,
                            currencySymbols[transaction.ticker] ||
                              transaction.currency
                          )
                        );
                      })()}
                    </td>
                    <td>
                      <div className="actions">
                        <button
                          className="edit_button"
                          onClick={() => onEdit(transaction)}
                        >
                          <Edit size={16} />
                        </button>
                        <button
                          className="delete_button"
                          onClick={() => setTransactionToDelete(transaction)}
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        <div style={{ marginTop: 20 }}>
          <Pagination>
            <PaginationContent>
              <PaginationItem>
                <PaginationPrevious
                  onClick={handlePrevious}
                  className={
                    currentPage === 1 ? "pointer-events-none opacity-50" : ""
                  }
                />
              </PaginationItem>

              {pages.map((page, index) =>
                typeof page === "number" ? (
                  <PaginationItem key={page}>
                    <PaginationLink
                      isActive={page === currentPage}
                      onClick={() => setCurrentPage(page)}
                    >
                      {page}
                    </PaginationLink>
                  </PaginationItem>
                ) : (
                  <PaginationItem key={`ellipsis-${index}`}>
                    <span className="px-2 text-muted-foreground">…</span>
                  </PaginationItem>
                )
              )}

              <PaginationItem>
                <PaginationNext
                  onClick={handleNext}
                  className={
                    currentPage === totalPages
                      ? "pointer-events-none opacity-50"
                      : ""
                  }
                />
              </PaginationItem>
            </PaginationContent>
          </Pagination>
        </div>
      </div>

      {transactionToDelete && (
        <AlertDialog
          open={!!transactionToDelete}
          onOpenChange={(open) => !open && setTransactionToDelete(null)}
        >
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Supprimer la transaction ?</AlertDialogTitle>
              <AlertDialogDescription>
                ⚠️ Cette action est <strong>irréversible</strong>. La
                transaction sera définitivement supprimée.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel style={{ cursor: "pointer" }}>
                Annuler
              </AlertDialogCancel>
              <AlertDialogAction
                onClick={confirmDeleteTransaction}
                style={{ cursor: "pointer" }}
              >
                Supprimer
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      )}
    </div>
  );
};

export default TransactionTable;
