import React, { useState } from "react";
import { SquareArrowDown } from "lucide-react";

import type { Transaction } from "../type";

import "../../../static/css/portfolio/transaction/TransactionFilter.css";

interface TransactionFilterProps {
  column: keyof Transaction;
  options: string[];
  selectedValues: string[];
  onChange: (values: string[]) => void;
  onSortChange?: (order: "asc" | "desc" | null) => void;
  openedFilter: keyof Transaction | null;
  setOpenedFilter: (col: keyof Transaction | null) => void;
}

const TransactionFilter: React.FC<TransactionFilterProps> = ({
  column,
  options,
  selectedValues,
  onChange,
  onSortChange,
  openedFilter,
  setOpenedFilter,
}) => {
  const [sortOrder, setSortOrder] = useState<"asc" | "desc" | null>(null);
  const showFilter = openedFilter === column;

  const toggleValue = (value: string) => {
    if (selectedValues.includes(value)) {
      onChange(selectedValues.filter((v) => v !== value));
    } else {
      onChange([...selectedValues, value]);
    }
  };

  const handleSortClick = (order: "asc" | "desc") => {
    const newOrder = sortOrder === order ? null : order;
    setSortOrder(newOrder);
    onSortChange?.(newOrder);
  };

  const handleToggleFilter = () => {
    if (showFilter) {
      setOpenedFilter(null);
    } else {
      setOpenedFilter(column);
    }
  };

  const getDisplayLabel = (value: string) => {
    const labelMap: Record<string, string> = {
      buy: "Achat",
      sell: "Vente",
      dividend: "Dividende",
      interest: "Intérêt",
      deposit: "Rentrer d'argent",
      withdrawal: "Sortie d'argent",
    };
    return labelMap[value] || value;
  };

  const hasActiveFilter =
    selectedValues.length > 0 && selectedValues.length < options.length;

  return (
    <div style={{ position: "relative" }}>
      <div
        onClick={handleToggleFilter}
        className={`filter-button ${hasActiveFilter ? "active-filter" : ""}`}
        style={{ display: "flex", gap: "5px" }}
      >
        <SquareArrowDown size={20} style={{ cursor: "pointer" }} />
      </div>

      {showFilter && (
        <div className="filter-panel">
          <div className="filter-content">
            <div className="filter-values">
              <div className="sort-buttons">
                <button
                  onClick={() => handleSortClick("asc")}
                  className={sortOrder === "asc" ? "active-sort-button" : ""}
                >
                  Trier dans l'ordre croissant
                </button>
                <button
                  onClick={() => handleSortClick("desc")}
                  className={sortOrder === "desc" ? "active-sort-button" : ""}
                >
                  Trier dans l'ordre décroissant
                </button>
              </div>

              <label>
                <input
                  type="checkbox"
                  checked={selectedValues.length === options.length}
                  onChange={(e) => onChange(e.target.checked ? options : [])}
                />
                Tout sélectionner
              </label>

              {options.map((val) => (
                <label key={val}>
                  <input
                    type="checkbox"
                    checked={selectedValues.includes(val)}
                    onChange={() => toggleValue(val)}
                  />
                  {getDisplayLabel(val)}
                </label>
              ))}
            </div>
          </div>

          <div className="filter-actions">
            <button onClick={() => setOpenedFilter(null)}>Fermer</button>
          </div>
        </div>
      )}
    </div>
  );
};

export default TransactionFilter;
