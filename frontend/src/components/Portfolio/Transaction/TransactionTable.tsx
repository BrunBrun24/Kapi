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
import Swal from "sweetalert2";

import api from "../../../api";
import TransactionFilter from "./TransactionFilter";
import type { Ticker, Transaction } from "../type";

import "../../../static/css/portfolio/transaction/TransactionTable.css";

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
  const itemsPerPage = 30;

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

  const handleDeleteTransaction = async (transactionId: string) => {
    const result = await Swal.fire({
      title: "Êtes-vous sûr ?",
      text: "⚠️ Cette action est irréversible. La transaction sera supprimée.",
      icon: "warning",
      showCancelButton: true,
      confirmButtonColor: "#3085d6",
      cancelButtonColor: "#d33",
      confirmButtonText: "Oui, supprimer",
      cancelButtonText: "Annuler",
    });

    if (result.isConfirmed) {
      try {
        await api.delete(`api/portfolio-transaction/${transactionId}/delete`);
        onRefresh();
      } catch (error) {
        console.error("Erreur lors de la suppression de la transaction", error);
        Swal.fire({
          title: "Erreur",
          text: "Une erreur est survenue lors de la suppression.",
          icon: "error",
        });
      }
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

  return (
    <div>
      <div className="table_wrapper">
        <div style={{ minHeight: 495, maxHeight: 495, overflowY: "auto" }}>
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
                        ? formatNumberWithSymbol(
                            transaction.quantity,
                            currencySymbols[transaction.ticker] ||
                              transaction.currency
                          )
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
                          onClick={() =>
                            handleDeleteTransaction(transaction.id)
                          }
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
        <div className="pagination_controls">
          <button
            disabled={currentPage === 1}
            onClick={() => setCurrentPage((prev) => prev - 1)}
          >
            <MoveLeft size={12} />
          </button>
          <span>
            Page {currentPage} sur {totalPages}
          </span>
          <button
            disabled={currentPage === totalPages}
            onClick={() => setCurrentPage((prev) => prev + 1)}
          >
            <MoveRight size={12} />
          </button>
        </div>
      </div>
    </div>
  );
};

export default TransactionTable;
