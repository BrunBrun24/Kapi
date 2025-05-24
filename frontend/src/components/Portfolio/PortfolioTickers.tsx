import React, { useEffect, useState } from "react";
import { ChevronDown, ChevronUp, PlusCircle, Trash2 } from "lucide-react";
import Swal from "sweetalert2";

import api from "../../api";
import TransactionForm from "./Transaction/TransactionForm";
import type {
  Ticker,
  TickerNotInPortfolio,
  Currency,
  PortfolioIdProps,
} from "./type";

import "../../static/css/Portfolio/PortfolioTicker.css";
import "../../static/css/Portfolio/form.css";

const PortfolioTickers: React.FC<PortfolioIdProps> = ({
  selectedPortfolioId,
}) => {
  const [isTickerListOpen, setIsTickerListOpen] = useState(false);
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [tickersInPortfolio, setTickersInPortfolio] = useState<Ticker[]>([]);
  const [tickersNotInPortfolio, setTickersNotInPortfolio] = useState<
    TickerNotInPortfolio[]
  >([]);
  const [currencies, setCurrencies] = useState<Currency[]>([]);
  const [formData, setFormData] = useState({
    ticker: "",
    currency: "",
  });

  const [searchTicker, setSearchTicker] = useState("");
  const [searchCurrency, setSearchCurrency] = useState("");
  const [filteredTickers, setFilteredTickers] = useState<
    { ticker: string; name: string }[]
  >([]);
  const [filteredCurrency, setFilteredCurrency] = useState<Currency[]>([]);

  const fetchTickersInPortfolio = async () => {
    try {
      if (!selectedPortfolioId) return;

      const res = await api.get(
        `/api/portfolio/${selectedPortfolioId}/tickers/`
      );
      const portfolioTickers: Ticker[] = res.data;

      const sortedTickers = portfolioTickers.sort((a: Ticker, b: Ticker) =>
        a.ticker.localeCompare(b.ticker)
      );

      setTickersInPortfolio(sortedTickers);
    } catch (error) {
      console.error("Erreur lors de la récupération des tickers", error);
    }
  };

  const fetchTickersNotInPortfolio = async () => {
    try {
      if (!selectedPortfolioId) {
        return;
      }
      const res = await api.get(
        `/api/portfolio/${selectedPortfolioId}/available-tickers/`
      );
      const portfolioTickers = res.data;
      setTickersNotInPortfolio(portfolioTickers);
    } catch (error) {
      console.error(
        "Erreur lors de la récupération des tickers qui ne sont pas associé au portefeuille",
        error
      );
    }
  };

  useEffect(() => {
    fetchTickersInPortfolio();
    fetchTickersNotInPortfolio();
  }, [selectedPortfolioId]);

  useEffect(() => {
    const fetchCurrency = async () => {
      try {
        const res = await api.get(`/api/currencies/`);
        const currencies = res.data;
        setCurrencies(currencies);
      } catch (error) {
        console.error("Erreur lors de la récupération des devises", error);
      }
    };

    fetchCurrency();
  }, []);

  // Filtrer les tickers en fonction de la recherche
  const handleSearchChangeTicker = (e: React.ChangeEvent<HTMLInputElement>) => {
    const query = e.target.value;
    setSearchTicker(query);

    // Filtrer les tickers par ticker ou par nom de société
    const filtered = tickersNotInPortfolio.filter(
      (ticker) =>
        ticker.ticker.toLowerCase().includes(query.toLowerCase()) ||
        ticker.name.toLowerCase().includes(query.toLowerCase())
    );

    setFilteredTickers(filtered.slice(0, 10)); // Limiter à 10 résultats
  };

  // Filtrer les devises en fonction de la recherche
  const handleSearchChangeCurrency = (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    const query = e.target.value;
    setSearchCurrency(query);

    setFilteredCurrency(currencies.slice(0, 10)); // Limiter à 10 résultats
  };

  const handleSelectTicker = (ticker: string) => {
    // Mettre à jour le champ de recherche avec le ticker sélectionné
    setSearchTicker(`${ticker}`);

    // Mettre à jour les valeurs de formData avec le ticker et le nom de la société
    setFormData((prev) => ({
      ...prev,
      ticker,
    }));
    setFilteredTickers([]);
  };

  const handleSelectCurrency = (currency: string) => {
    // Mettre à jour le champ de recherche avec le ticker sélectionné
    setSearchCurrency(`${currency}`);

    // Mettre à jour les valeurs de formData avec le ticker et le nom de la société
    setFormData((prev) => ({
      ...prev,
      currency,
    }));
    setFilteredCurrency([]);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedPortfolioId) return;

    try {
      // Utilisation de axios pour envoyer la requête POST
      const response = await api.post("/api/portfolio/ticker/", {
        portfolio: selectedPortfolioId,
        ticker: formData.ticker.toUpperCase(),
        currency: formData.currency,
      });

      // Vérification de la réponse
      if (response.status !== 201) {
        throw new Error("Failed to add ticker");
      }

      // Réinitialisation du formulaire
      setFormData({
        ticker: "",
        currency: "",
      });
      setSearchTicker("");
      setSearchCurrency("");
      setIsFormOpen(false);
      await fetchTickersInPortfolio();
      await fetchTickersNotInPortfolio();
    } catch (error) {
      console.error("Error submitting ticker:", error);
    }
  };

  const handleDeleteTicker = async (ticker: string) => {
    const result = await Swal.fire({
      title: "Êtes-vous sûr ?",
      text: "⚠️ Cette action est irréversible. Toutes les transactions liées à cette entreprise seront supprimées.",
      icon: "warning",
      showCancelButton: true,
      confirmButtonColor: "#3085d6",
      cancelButtonColor: "#d33",
      confirmButtonText: "Oui, supprimer",
      cancelButtonText: "Annuler",
    });

    if (result.isConfirmed) {
      try {
        await api.delete(
          `api/portfolio/${selectedPortfolioId}/ticker/${ticker}/delete/`
        );
        await fetchTickersInPortfolio();
        await fetchTickersNotInPortfolio();

        await Swal.fire({
          title: "Supprimé !",
          text: "L'entreprise a bien été supprimé.",
          icon: "success",
        });
      } catch (error) {
        console.error("Erreur lors de la suppression de l'entreprise", error);
        Swal.fire({
          title: "Erreur",
          text: "Une erreur est survenue lors de la suppression.",
          icon: "error",
        });
      }
    }
  };

  if (!selectedPortfolioId) {
    return;
  }

  return (
    <>
      <div className="container">
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

        {isFormOpen ? (
          <form onSubmit={handleSubmit} className="form-fields">
            <div className="form-grid-2">
              <div>
                <label className="form-label">
                  Rechercher un Ticker ou une Entreprise
                </label>
                <div style={{ position: "relative" }}>
                  <input
                    type="text"
                    value={searchTicker}
                    onChange={handleSearchChangeTicker}
                    placeholder="ex: AAPL"
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
              </div>
            </div>
            <div className="form-submit">
              <button type="submit" className="form-button">
                Ajouter un ticker
              </button>
            </div>
          </form>
        ) : !isFormOpen && tickersInPortfolio.length === 0 ? (
          <p className="placeholder">
            Sélectionnez un ticker pour pouvoir ajouter des transactions
          </p>
        ) : (
          isTickerListOpen && (
            <div className="portfolio-ticker-container">
              {tickersInPortfolio.map((t) => (
                <div key={t.ticker} className="portfolio-ticker">
                  <img
                    src={t.logo}
                    alt={`Logo de ${t.ticker}`}
                    className="ticker-logo"
                  />
                  <div className="portfolio-ticker-data">
                    <p className="ticker-symbol">{t.ticker}</p>
                    <p className="ticker-currency">{t.currency}</p>
                  </div>
                  <button
                    className="ticker-remove-button"
                    onClick={() => handleDeleteTicker(t.ticker)}
                    aria-label={`Supprimer ${t.ticker}`}
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              ))}
            </div>
          )
        )}
      </div>

      {/* Si aucun ticker n'a été selectionné alors ne pas afficher les transactions */}
      {tickersInPortfolio.length !== 0 && (
        <TransactionForm selectedPortfolioId={selectedPortfolioId} />
      )}
    </>
  );
};

export default PortfolioTickers;
