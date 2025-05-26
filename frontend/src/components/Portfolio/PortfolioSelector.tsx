import React, { useEffect, useState } from "react";
import { Trash2, Edit, PlusCircle } from "lucide-react";
import Swal from "sweetalert2";

import api from "../../api";
import PortfolioTickers from "./PortfolioTickers";
import type { Portfolio } from "./type";

import "../../static/css/portfolio/PortfolioSelector.css";
import "../../static/css/portfolio/form.css";

const PortfolioSelector: React.FC = () => {
  const [portfolios, setPortfolios] = useState<Portfolio[]>([]);
  const [selectedPortfolioId, setSelectedPortfolioId] = useState<string | null>(
    null
  );
  const [isCreating, setIsCreating] = useState(false);
  const [newPortfolioName, setNewPortfolioName] = useState("");

  useEffect(() => {
    const fetchPortfolios = async () => {
      try {
        const res = await api.get("/api/portfolios/");
        const userPortfolios = res.data;
        setPortfolios(userPortfolios);
        if (userPortfolios.length > 0) {
          setSelectedPortfolioId(userPortfolios[0].id);
        }
      } catch (error) {
        console.error(
          "Erreur lors de la récupération des portefeuilles",
          error
        );
      }
    };

    fetchPortfolios();
  }, []);

  const handleSelectPortfolio = (id: string) => {
    setSelectedPortfolioId(id);
  };

  const handleCreatePortfolio = async () => {
    if (newPortfolioName.trim() === "") return;

    const newPortfolioData = {
      name: newPortfolioName.trim(),
    };

    try {
      const res = await api.post("/api/portfolio/create/", newPortfolioData);
      const newPortfolio: Portfolio = res.data;
      const updated = [...portfolios, newPortfolio];
      setPortfolios(updated);
      setSelectedPortfolioId(newPortfolio.id);
      setNewPortfolioName("");
      setIsCreating(false);
    } catch (error) {
      console.error("Erreur lors de la création du portefeuille", error);
    }
  };

  const handleDeletePortfolio = async (id: string) => {
    const result = await Swal.fire({
      title: "Êtes-vous sûr ?",
      text: "⚠️ Cette action est irréversible. Toutes les transactions liées à ce portefeuille seront supprimées.",
      icon: "warning",
      showCancelButton: true,
      confirmButtonColor: "#3085d6",
      cancelButtonColor: "#d33",
      confirmButtonText: "Oui, supprimer",
      cancelButtonText: "Annuler",
    });

    if (result.isConfirmed) {
      try {
        await api.delete(`/api/portfolios/${id}/delete/`);
        setPortfolios((prev) => prev.filter((p) => p.id !== id));
        setSelectedPortfolioId(null);
      } catch (error) {
        console.error("Erreur lors de la suppression du portefeuille", error);
        Swal.fire({
          title: "Erreur",
          text: "Une erreur est survenue lors de la suppression.",
          icon: "error",
        });
      }
    }
  };

  const handleEditPortfolio = async (id: string, currentName: string) => {
    const { value: formValues } = await Swal.fire({
      title: "Modifier le nom du portefeuille",
      html: `<input id="swal-input1" class="swal2-input" placeholder="Nom du portefeuille" value="${currentName}">`,
      focusConfirm: false,
      showCancelButton: true,
      confirmButtonText: "Enregistrer",
      cancelButtonText: "Annuler",
      preConfirm: () => {
        const name = (
          document.getElementById("swal-input1") as HTMLInputElement
        ).value;
        if (!name) {
          Swal.showValidationMessage("Tous les champs sont requis");
          return;
        }
        return { name };
      },
    });

    if (formValues) {
      try {
        const response = await api.put(`/api/portfolio/${id}/update/`, {
          name: formValues.name,
        });

        const updatedPortfolio = response.data;
        setPortfolios((prev) =>
          prev.map((p) => (p.id === id ? updatedPortfolio : p))
        );

        Swal.fire({
          title: "Modifié !",
          text: "Le portefeuille a été mis à jour.",
          icon: "success",
        });
      } catch (error) {
        console.error("Erreur lors de la mise à jour", error);
        Swal.fire({
          title: "Erreur",
          text: "Impossible de modifier le portefeuille.",
          icon: "error",
        });
      }
    }
  };

  return (
    <>
      <div className="container">
        <div className="portfolio-heading">
          <h2 className="form-title">Portefeuilles</h2>
          <button
            onClick={() => setIsCreating(!isCreating)}
            className="form-toggle"
          >
            {isCreating ? (
              "Retour"
            ) : (
              <div className="form-toggle-content">
                <PlusCircle size={18} className="form-icon" />
                <span>Nouveau portefeuille</span>
              </div>
            )}
          </button>
        </div>

        {portfolios.length === 0 && !isCreating ? (
          <div className="portfolio-empty">
            <p className="portfolio-empty-text">
              Vous n'avez pas encore de portefeuille
            </p>
          </div>
        ) : (
          <>
            {!isCreating ? (
              <div className="portfolio-list">
                {portfolios.map((portfolio) => (
                  <div
                    key={portfolio.id}
                    className={`portfolio-item ${
                      selectedPortfolioId === portfolio.id
                        ? "portfolio-item--selected"
                        : "portfolio-item--hoverable"
                    }`}
                    onClick={() => handleSelectPortfolio(portfolio.id)}
                  >
                    <div>
                      <h3 className="portfolio-name">{portfolio.name}</h3>
                    </div>

                    <div className="portfolio-actions">
                      <button
                        className="portfolio-edit-button"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleEditPortfolio(portfolio.id, portfolio.name);
                        }}
                      >
                        <Edit size={16} />
                      </button>

                      <button
                        className="portfolio-delete-button"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDeletePortfolio(portfolio.id);
                        }}
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <form onSubmit={handleCreatePortfolio} className="form-fields">
                <div className="form-block">
                  <div>
                    <label className="form-label">Nom du portefeuille</label>
                    <input
                      type="text"
                      value={newPortfolioName}
                      onChange={(e) => setNewPortfolioName(e.target.value)}
                      placeholder="Entrez un nom de portefeuille"
                      className="form-input"
                      required
                    />
                  </div>
                </div>

                <div className="form-submit">
                  <button type="submit" className="form-button">
                    Ajouter un portefeuille
                  </button>
                </div>
              </form>
            )}
          </>
        )}
      </div>

      <PortfolioTickers selectedPortfolioId={selectedPortfolioId} />
    </>
  );
};

export default PortfolioSelector;
