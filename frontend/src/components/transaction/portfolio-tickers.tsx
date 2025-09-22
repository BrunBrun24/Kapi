"use client";

import React, { useEffect, useState, useRef } from "react";
import { ChevronDown, ChevronUp, PlusCircle, Trash2 } from "lucide-react";
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
import TransactionForm from "./transaction-form";
import type {
  Ticker,
  TickerNotInPortfolio,
} from "@/components/transaction/type/index";

import "@/static/css/components/transaction/portfolio-tickers.css";
import "@/static/css/components/transaction/form.css";

export interface PortfolioIdProps {
  selectedPortfolioId: string | null;
}

const PortfolioTickers: React.FC<PortfolioIdProps> = ({
  selectedPortfolioId,
}) => {
  const [isTickerListOpen, setIsTickerListOpen] = useState(true);
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [tickersInPortfolio, setTickersInPortfolio] = useState<Ticker[]>([]);
  const [tickersNotInPortfolio, setTickersNotInPortfolio] = useState<
    TickerNotInPortfolio[]
  >([]);
  const [formData, setFormData] = useState({ ticker: "", currencies: "" });

  const [searchTicker, setSearchTicker] = useState("");
  const [filteredTickers, setFilteredTickers] = useState<
    TickerNotInPortfolio[]
  >([]);

  const [availableCurrencies, setAvailableCurrencies] = useState<string[]>([]);
  const [searchCurrency, setSearchCurrency] = useState("");
  const [filteredCurrency, setFilteredCurrency] = useState<string[]>([]);

  const [tickerToDelete, setTickerToDelete] = useState<{
    ticker: string;
    currency: string;
  } | null>(null);

  // Refs pour gérer le clic en dehors
  const tickerDropdownRef = useRef<HTMLDivElement>(null);
  const currencyDropdownRef = useRef<HTMLDivElement>(null);

  const fetchTickersInPortfolio = async () => {
    if (!selectedPortfolioId) return;
    try {
      const res = await api.get(
        `/api/portfolios/${selectedPortfolioId}/tickers/`
      );
      const sortedTickers = res.data.sort((a: Ticker, b: Ticker) =>
        a.ticker.localeCompare(b.ticker)
      );
      setTickersInPortfolio(sortedTickers);
    } catch (error) {
      console.error("Erreur lors de la récupération des tickers", error);
    }
  };

  const fetchTickersNotInPortfolio = async () => {
    if (!selectedPortfolioId) return;
    try {
      const res = await api.get(
        `/api/portfolios/${selectedPortfolioId}/tickers/available/`
      );
      setTickersNotInPortfolio(res.data);
    } catch (error) {
      console.error(
        "Erreur lors de la récupération des tickers non associés",
        error
      );
    }
  };

  useEffect(() => {
    fetchTickersInPortfolio();
    fetchTickersNotInPortfolio();
  }, [selectedPortfolioId]);

  // Gestion recherche tickers
  const handleSearchChangeTicker = (e: React.ChangeEvent<HTMLInputElement>) => {
    const query = e.target.value;
    setSearchTicker(query);

    const filtered = tickersNotInPortfolio.filter(
      (t) =>
        t.ticker.toLowerCase().includes(query.toLowerCase()) ||
        t.name.toLowerCase().includes(query.toLowerCase())
    );
    setFilteredTickers(filtered.slice(0, 10));
  };

  const handleSelectTicker = (ticker: TickerNotInPortfolio) => {
    setSearchTicker(ticker.ticker);
    setFormData({ ticker: ticker.ticker, currencies: "" });

    const currencies = Array.isArray(ticker.currencies)
      ? ticker.currencies
      : [];
    setAvailableCurrencies(currencies);
    setFilteredTickers([]);
    setSearchCurrency("");

    if (currencies.length === 1) {
      setSearchCurrency(currencies[0]);
      setFormData((prev) => ({ ...prev, currencies: currencies[0] }));
      setFilteredCurrency([]);
    } else {
      setFilteredCurrency([]);
    }
  };

  // Gestion recherche devises
  const handleSearchChangeCurrency = (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    const query = e.target.value.toUpperCase();
    setSearchCurrency(query);

    const filtered = availableCurrencies.filter((cur) =>
      cur.toUpperCase().includes(query)
    );
    setFilteredCurrency(filtered.slice(0, 10));
  };

  const handleSelectCurrency = (currencies: string) => {
    setSearchCurrency(currencies);
    setFormData((prev) => ({ ...prev, currencies }));
    setFilteredCurrency([]);
  };

  // Clic en dehors pour fermer les dropdowns
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        tickerDropdownRef.current &&
        !tickerDropdownRef.current.contains(event.target as Node)
      ) {
        setFilteredTickers([]);
      }
      if (
        currencyDropdownRef.current &&
        !currencyDropdownRef.current.contains(event.target as Node)
      ) {
        setFilteredCurrency([]);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

  // Submit
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedPortfolioId) return;

    try {
      const response = await api.post(
        `/api/portfolios/${selectedPortfolioId}/tickers/`,
        {
          ticker: formData.ticker.toUpperCase(),
          currency: formData.currencies,
        }
      );

      if (response.status !== 201) throw new Error("Failed to add ticker");

      setFormData({ ticker: "", currencies: "" });
      setSearchTicker("");
      setSearchCurrency("");
      setIsFormOpen(false);

      // Rafraîchir les tickers
      await fetchTickersInPortfolio();
      await fetchTickersNotInPortfolio();
    } catch (error) {
      console.error("Error submitting ticker:", error);
    }
  };

  // Delete
  const confirmDeleteTicker = async () => {
    if (!tickerToDelete || !selectedPortfolioId) return;
    try {
      await api.delete(
        `/api/portfolios/${selectedPortfolioId}/tickers/${tickerToDelete.ticker}/${tickerToDelete.currency}/`
      );

      await fetchTickersInPortfolio();
      await fetchTickersNotInPortfolio();
    } catch (error) {
      console.error("Erreur lors de la suppression du ticker", error);
    } finally {
      setTickerToDelete(null);
    }
  };

  if (!selectedPortfolioId) return null;

  return (
    <>
      <div className="portfolio-container">
        <div className="form-header">
          <div
            className="portfolio-ticker-header clickable"
            onClick={() => setIsTickerListOpen((prev) => !prev)}
          >
            <h2 className="form-title">Tickers</h2>
            {isTickerListOpen ? (
              <ChevronUp size={18} className="chevron-icon" />
            ) : (
              <ChevronDown size={18} className="chevron-icon" />
            )}
          </div>

          <button
            onClick={() => setIsFormOpen(!isFormOpen)}
            className="form-toggle"
          >
            {isFormOpen ? (
              "Retour"
            ) : (
              <div className="form-toggle-content">
                <PlusCircle size={18} className="form-icon" />
                <span>Ajouter un ticker</span>
              </div>
            )}
          </button>
        </div>

        {isFormOpen && (
          <form onSubmit={handleSubmit} className="form-fields">
            <div className="form-grid-2">
              {/* Dropdown Tickers */}
              <div ref={tickerDropdownRef}>
                <label className="form-label">
                  Rechercher un Ticker ou une Entreprise
                </label>
                <div style={{ position: "relative" }}>
                  <input
                    type="text"
                    value={searchTicker}
                    onChange={handleSearchChangeTicker}
                    onFocus={() =>
                      setFilteredTickers(tickersNotInPortfolio.slice(0, 10))
                    }
                    placeholder="ex: AAPL"
                    className="form-input"
                  />
                  {filteredTickers.length > 0 && (
                    <ul className="dropdown-list">
                      {filteredTickers.map((ticker) => (
                        <li
                          key={ticker.ticker}
                          onClick={() => handleSelectTicker(ticker)}
                          className="dropdown-item"
                        >
                          {ticker.ticker} ({ticker.name})
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              </div>

              {/* Dropdown Devise */}
              <div ref={currencyDropdownRef}>
                <label className="form-label">Devise</label>
                <div style={{ position: "relative" }}>
                  <input
                    type="text"
                    value={searchCurrency}
                    onChange={handleSearchChangeCurrency}
                    onFocus={() => setFilteredCurrency(availableCurrencies)}
                    placeholder="ex: EUR, USD..."
                    className="form-input"
                    disabled={availableCurrencies.length === 0}
                  />
                  {filteredCurrency.length > 0 && (
                    <ul className="dropdown-list">
                      {filteredCurrency.map((cur) => (
                        <li
                          key={cur}
                          onClick={() => handleSelectCurrency(cur)}
                          className="dropdown-item"
                        >
                          {cur}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              </div>
            </div>
            <div className="form-submit">
              <button type="submit" className="form-button">
                Ajouter un ticker
              </button>
            </div>
          </form>
        )}

        {!isFormOpen && tickersInPortfolio.length === 0 && (
          <p className="placeholder">
            Sélectionnez un ticker pour pouvoir ajouter des transactions
          </p>
        )}

        {isTickerListOpen && tickersInPortfolio.length > 0 && !isFormOpen && (
          <div className="portfolio-ticker-container">
            {tickersInPortfolio.map((t) => (
              <div
                key={`${t.ticker}-${t.currency}`}
                className="portfolio-ticker"
              >
                <img
                  src={t.logo}
                  alt={`Logo de ${t.ticker}`}
                  className="ticker-logo"
                />
                <div className="portfolio-ticker-data">
                  <p className="ticker-symbol">{t.ticker}</p>
                  <p className="ticker-currencies">{t.currency}</p>
                </div>
                <button
                  className="ticker-remove-button"
                  onClick={() =>
                    setTickerToDelete({
                      ticker: t.ticker,
                      currency: t.currency,
                    })
                  }
                  aria-label={`Supprimer ${t.ticker}`}
                >
                  <Trash2 size={16} />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {tickersInPortfolio.length !== 0 && (
        <TransactionForm
          selectedPortfolioId={selectedPortfolioId}
          tickersInPortfolio={tickersInPortfolio}
        />
      )}

      {tickerToDelete && (
        <AlertDialog
          open={!!tickerToDelete}
          onOpenChange={(open) => !open && setTickerToDelete(null)}
        >
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Supprimer le ticker ?</AlertDialogTitle>
              <AlertDialogDescription>
                ⚠️ Cette action est <strong>irréversible</strong>. Les
                transactions liées à ce ticker seront définitivement supprimées.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel style={{ cursor: "pointer" }}>
                Annuler
              </AlertDialogCancel>
              <AlertDialogAction
                onClick={confirmDeleteTicker}
                style={{ cursor: "pointer" }}
              >
                Supprimer
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      )}
    </>
  );
};

export default PortfolioTickers;
