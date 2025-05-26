import React, { useState, useEffect } from "react";
import { PlusCircle } from "lucide-react";

import api from "../../../api";
import TransactionTable from "./TransactionTable";
import ExcelUploader from "../file/ExcelUploader";
import type { Ticker, Transaction } from "../type";

import "../../../static/css/portfolio/form.css";
import { useCurrencySearch } from "../../hook/useCurrencySearch";

export interface PortfolioIdProps {
  selectedPortfolioId: string;
  tickersInPortfolio: Ticker[];
}

const TransactionForm: React.FC<PortfolioIdProps> = ({
  selectedPortfolioId,
  tickersInPortfolio,
}) => {
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [formData, setFormData] = useState({
    ticker: "",
    operation: "buy",
    stock_price: 0,
    quantity: 0,
    amount: 0,
    date: new Date().toISOString().split("T")[0],
    fees: 0,
    currency: "",
  });

  const [tickers, setTickers] = useState<{ ticker: string; name: string }[]>(
    []
  );
  const [searchQuery, setSearchQuery] = useState("");
  const [filteredTickers, setFilteredTickers] = useState<
    { ticker: string; name: string }[]
  >([]);
  const [editMode, setEditMode] = useState(false);
  const [transactionId, setTransactionId] = useState<string | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);

  const {
    allCurrencies,
    searchCurrency,
    filteredCurrency,
    selectedCurrency,
    handleSearchChangeCurrency,
    handleSelectCurrency,
  } = useCurrencySearch();

  useEffect(() => {
    if (selectedCurrency) {
      setFormData((prev) => ({
        ...prev,
        currency: selectedCurrency,
      }));
    }
  }, [selectedCurrency]);

  const fetchTickers = async () => {
    if (!selectedPortfolioId) return;
    try {
      const response = await api.get(
        `/api/portfolio/${selectedPortfolioId}/tickers/`
      );
      setTickers(response.data);
    } catch (error) {
      console.error("Error fetching tickers:", error);
    }
  };

  useEffect(() => {
    fetchTickers();
  }, [selectedPortfolioId]);

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const query = e.target.value;
    setSearchQuery(query);
    const filtered = tickers.filter(
      (ticker) =>
        ticker.ticker.toLowerCase().includes(query.toLowerCase()) ||
        ticker.name.toLowerCase().includes(query.toLowerCase())
    );
    setFilteredTickers(filtered.slice(0, 10));
  };

  const handleSelectTicker = (ticker: string) => {
    setSearchQuery(`${ticker}`);
    setFormData((prev) => ({ ...prev, ticker }));
    setFilteredTickers([]);
  };

  const handleChange = (
    e: React.ChangeEvent<
      HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement
    >
  ) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: ["quantity", "amount", "fees", "stock_price"].includes(name)
        ? parseFloat(value) || 0
        : value,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedPortfolioId) return;

    const operation = formData.operation;
    const commonPayload = {
      operation: formData.operation,
      amount: formData.amount,
      date: formData.date,
      fees: formData.fees,
    };

    // Construction du payload selon l'opération
    let payload: any = { ...commonPayload };
    payload.portfolio = selectedPortfolioId;

    if (["buy", "sell"].includes(operation)) {
      payload.portfolio_ticker = formData.ticker.toUpperCase();
      payload.stock_price = formData.stock_price;
    } else if (["dividend"].includes(operation)) {
      payload.portfolio_ticker = formData.ticker.toUpperCase();
      payload.quantity = formData.quantity;
    } else if (["deposit", "withdrawal", "interest"].includes(operation)) {
      payload.currency = formData.currency;
    }

    try {
      if (editMode && transactionId) {
        const response = await api.put(
          `/api/portfolio-transaction/${transactionId}/update`,
          payload
        );
        if (response.status !== 200)
          throw new Error("Failed to update transaction");
      } else {
        const response = await api.post(
          "/api/portfolio-transaction/create/",
          payload
        );
        if (response.status !== 201)
          throw new Error("Failed to add transaction");
      }

      resetForm();
      setRefreshKey((prevKey) => prevKey + 1);
    } catch (error: any) {
      if (error.response) {
        console.error("❌ Erreur backend :", error.response.data);
      } else {
        console.error("❌ Erreur inconnue :", error.message);
      }
    }
  };

  const resetForm = () => {
    setFormData({
      ticker: "",
      operation: "buy",
      stock_price: 0,
      quantity: 0,
      amount: 0,
      date: new Date().toISOString().split("T")[0],
      fees: 0,
      currency: "",
    });
    setIsFormOpen(false);
    setEditMode(false);
    setTransactionId(null);
    handleSelectCurrency("");
  };

  const handleEditTransaction = (tx: Transaction) => {
    setIsFormOpen(true);
    setEditMode(true);
    setTransactionId(tx.id.toString());
    setFormData({
      ticker: tx.ticker,
      operation: tx.operation,
      stock_price: tx.stock_price,
      quantity: tx.quantity,
      amount: tx.amount,
      date: tx.date,
      fees: tx.fees ?? 0,
      currency: tx.currency,
    });
    setSearchQuery(tx.ticker);

    // 🔁 Convertir le symbole en code ISO si nécessaire
    const matchedCurrency = allCurrencies.find(
      (cur) => cur.label === tx.currency || cur.code === tx.currency
    );

    if (matchedCurrency) {
      handleSelectCurrency(matchedCurrency.code);
    } else {
      handleSelectCurrency(tx.currency); // fallback
    }
  };

  if (!selectedPortfolioId) return null;

  return (
    <div className="container">
      <div className="form-header">
        <h2 className="form-title">Transactions</h2>
        <button
          onClick={() => (isFormOpen ? resetForm() : setIsFormOpen(true))}
          className="form-toggle"
        >
          {isFormOpen ? (
            "Retour"
          ) : (
            <div className="form-toggle-content">
              <PlusCircle size={18} className="form-icon" />
              <span>Ajouter une transaction</span>
            </div>
          )}
        </button>
      </div>

      {isFormOpen ? (
        <form onSubmit={handleSubmit} className="form-fields">
          <div className="form-grid-2">
            <div>
              <label className="form-label">Type de transaction</label>
              <select
                name="operation"
                value={formData.operation}
                onChange={handleChange}
                className="form-input"
              >
                <option value="buy">Achat</option>
                <option value="sell">Vente</option>
                <option value="dividend">Dividende</option>
                <option value="interest">Intérêt</option>
                <option value="deposit">Rentrer d'argent</option>
                <option value="withdrawal">Sortie d'argent</option>
              </select>
            </div>
            <div>
              <label className="form-label">Date</label>
              <input
                type="date"
                name="date"
                value={formData.date}
                onChange={handleChange}
                className="form-input"
                required
              />
            </div>
          </div>

          {["buy", "sell", "dividend"].includes(formData.operation) && (
            <div className="form-grid-2">
              <div>
                <label className="form-label">
                  Rechercher un Ticker ou une Company
                </label>
                <div style={{ position: "relative" }}>
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={handleSearchChange}
                    placeholder="Tapez un ticker ou une company"
                    className="form-input"
                  />
                  {filteredTickers.length > 0 && (
                    <ul className="dropdown-list">
                      {filteredTickers.map((ticker) => (
                        <li
                          key={ticker.ticker}
                          onClick={() => handleSelectTicker(ticker.ticker)}
                          className="dropdown-item"
                        >
                          {ticker.ticker} ({ticker.name})
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              </div>
              <div>
                <label className="form-label">Montant</label>
                <input
                  type="number"
                  name="amount"
                  value={formData.amount}
                  onChange={handleChange}
                  min="0.01"
                  step="0.01"
                  className="form-input"
                  required
                />
              </div>
            </div>
          )}

          {["buy", "sell"].includes(formData.operation) && (
            <div className="form-grid-2">
              <div>
                <label className="form-label">Prix de l'action</label>
                <input
                  type="number"
                  name="stock_price"
                  value={formData.stock_price}
                  onChange={handleChange}
                  min="0.01"
                  step="0.01"
                  className="form-input"
                  required
                />
              </div>
              <div>
                <label className="form-label">Frais/Commission</label>
                <input
                  type="number"
                  name="fees"
                  value={formData.fees}
                  onChange={handleChange}
                  min="0"
                  step="0.01"
                  className="form-input"
                />
              </div>
            </div>
          )}

          {formData.operation === "dividend" && (
            <div className="form-grid-2">
              <div>
                <label className="form-label">Quantité</label>
                <input
                  type="number"
                  name="quantity"
                  value={formData.quantity}
                  onChange={handleChange}
                  min="0.00001"
                  step="0.000001"
                  className="form-input"
                />
              </div>
              <div>
                <label className="form-label">Frais/Commission</label>
                <input
                  type="number"
                  name="fees"
                  value={formData.fees}
                  onChange={handleChange}
                  min="0"
                  step="0.01"
                  className="form-input"
                />
              </div>
            </div>
          )}

          {["deposit", "withdrawal", "interest"].includes(
            formData.operation
          ) && (
            <>
              <div className="form-grid-2">
                <div>
                  <label className="form-label">Montant</label>
                  <input
                    type="number"
                    name="amount"
                    value={formData.amount}
                    onChange={handleChange}
                    min="0.01"
                    step="0.01"
                    className="form-input"
                    required
                  />
                </div>
                <div>
                  <label className="form-label">Frais/Commission</label>
                  <input
                    type="number"
                    name="fees"
                    value={formData.fees}
                    onChange={handleChange}
                    min="0"
                    step="0.01"
                    className="form-input"
                  />
                </div>
              </div>
              <div style={{ position: "relative" }}>
                <label className="form-label">Devise</label>
                <input
                  type="text"
                  value={searchCurrency}
                  onChange={handleSearchChangeCurrency}
                  placeholder="ex: (EUR, USD, ...)"
                  className="form-input"
                />
                {filteredCurrency.length > 0 && (
                  <ul className="dropdown-list">
                    {filteredCurrency.map((cur) => (
                      <li
                        key={cur.code}
                        onClick={() => handleSelectCurrency(cur.code)}
                        className="dropdown-item"
                      >
                        {cur.code}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </>
          )}

          <div className="form-footer">
            <div className="form-footer-left">
              <ExcelUploader
                selectedPortfolioId={selectedPortfolioId}
                onImportSuccess={() => {
                  setIsFormOpen(false);
                  setRefreshKey((prev) => prev + 1);
                }}
              />
            </div>
            <div className="form-footer-right">
              <button type="submit" className="form-button">
                {editMode
                  ? "Mettre à jour la transaction"
                  : "Ajouter une transaction"}
              </button>
            </div>
          </div>
        </form>
      ) : (
        <TransactionTable
          selectedPortfolioId={selectedPortfolioId}
          onEdit={handleEditTransaction}
          refreshKey={refreshKey}
          onRefresh={() => setRefreshKey((prev) => prev + 1)}
          tickersInPortfolio={tickersInPortfolio}
        />
      )}
    </div>
  );
};

export default TransactionForm;
